import re
import ipaddress
from typing import List, Optional
from f5.bigip import ManagementRoot
from sqlalchemy.orm import Session

from ..dao import vipaddr as VIPAddrDao
from ..config import get_settings
from ..models.bigip import PoolModel, MemberModel, VirtualServerModel
from ..errors import (
    PoolNotFoundException,
    VServerNotFoundException,
    VServerNothingToChangeException,
    NodeNotFoundException,
)


class Bigip:
    env = None
    mgmt = None
    configs = get_settings()

    def __init__(self):
        config = self.configs
        # expired 를 모르겠다.
        # transaction 마다 인증을 거쳐서 사용하는 것이 더 나을 수도 있겠다.
        if config.bigip_enabled == "true":
            self.mgmt = ManagementRoot(
                config.bigip_host, config.bigip_username, config.bigip_password
            )

    def find_node(self, name: str, partition: str):
        return Node(self.mgmt).find(name=name, partition=partition)

    def create_node(self, name: str, partition: str, address: str, description=None):
        return Node(self.mgmt).create(
            name=name, partition=partition, address=address, description=description
        )

    def delete_node(self, name: str, partition: str = "Common"):
        Node(self.mgmt).delete(name=name, partition=partition)

    def delete_nodes(self, query: str):
        wmp_node = Node(self.mgmt)
        nodes = wmp_node.search_by_name(q=query)
        names = []
        for node in nodes:
            names.append(node.name)
            node.delete()

        return names

    def get_pools_by_node_name(self, name: str):
        return Pool(self.mgmt).search_by_node_name(name=name)

    def create_pool(self, pool: PoolModel, params):
        wmp_pool = Pool(self.mgmt)
        return wmp_pool.find_or_create(pool=pool, params=params)

    def find_pool(self, pool: PoolModel):
        found = Pool(self.mgmt).find(pool)
        if not found:
            raise PoolNotFoundException(f"Pool not found: {pool.name}")

        return found

    def get_pool_members(self, pool):
        return pool.members_s.get_collection()

    def update_pool_members(self, pool, members: List[MemberModel]):
        old_members = self.get_pool_members(pool=pool)

        a_seen = {}
        for member in old_members:
            a_seen[member.name] = True

        b_seen = {}
        for member in members:
            b_seen[member.name] = True

        ab_seen = {}
        delete_target = []
        for name in a_seen.keys():
            if name in b_seen:
                ab_seen[name] = True
            else:
                delete_target.append(name)

        create_target = []
        for name in b_seen.keys():
            if not name in ab_seen:
                create_target.append(name)

        wmp_pool = Pool(self.mgmt)
        for target in delete_target:
            wmp_pool.delete_member(pool=pool, member=MemberModel(name=target))

        for target in create_target:
            wmp_pool.add_member(pool=pool, member=MemberModel(name=target))

        return {"added": create_target, "deleted": delete_target}

    def delete_pool(self, pool: PoolModel):
        Pool(self.mgmt).delete(pool=pool)

    def create_pool_members(self, pool, members: List[MemberModel]):
        created = []
        for memberModel in members:
            if pool.members_s.members.exists(
                name=memberModel.name, partition=pool.partition
            ):
                raise Exception(f"member already exists: {memberModel.name}")

            created.append(
                pool.members_s.members.create(
                    name=memberModel.name, partition=pool.partition
                )
            )

        return created

    def delete_pool_members(self, pool, members: List[MemberModel]):
        deleted = []
        wmp_pool = Pool(self.mgmt)
        for memberModel in members:
            wmp_pool.delete_member(pool=pool, member=memberModel)
            deleted.append(memberModel.name)
        return deleted

    def delete_pool_member(self, pool, member: str):
        deleted = []
        wmp_pool = Pool(self.mgmt)
        wmp_pool.delete_member(pool=pool, member=MemberModel(name=member))
        deleted.append(member)
        return deleted

    def enable_pool_member(self, pool, member: str):
        enabled = []
        wmp_pool = Pool(self.mgmt)
        wmp_pool.enable_member(pool=pool, member=MemberModel(name=member))
        enabled.append(member)
        return enabled

    def disable_pool_member(self, pool, member: str):
        disabled = []
        wmp_pool = Pool(self.mgmt)
        wmp_pool.disable_member(pool=pool, member=MemberModel(name=member))
        disabled.append(member)
        return disabled

    def find_vserver(self, name: str, partition: str = "Common"):
        return Virtual(self.mgmt).find(name, partition=partition)

    def create_vserver(self, vserver: VirtualServerModel):
        pool = self.find_pool(PoolModel(name=vserver.pool, partition=vserver.partition))
        if not pool:
            raise PoolNotFoundException(
                f"pool not found: {vserver.pool}@{vserver.partition}"
            )

        return Virtual(self.mgmt).create(vserver=vserver)

    def delete_vserver(self, name: str, partition: str = "Common"):
        Virtual(self.mgmt).delete(name=name, partition=partition)

    def update_vserver_vip(
        self, hostname: str, vip: str, db: Session, partition: str = "Common"
    ):
        virtual = Virtual(self.mgmt)

        origin_vip = None
        for port in [80, 443]:
            name = f"{hostname}_{port}"
            vserver = self.find_vserver(name=name, partition=partition)
            if not vserver:
                raise VServerNotFoundException(f"VServer not found: {name}")
            destination = vserver.destination
            origin_vip = destination.split("/")[-1].split(":")[0]
            if origin_vip == vip:
                raise VServerNothingToChangeException(f"{name} already has vip: {vip}")

            virtual.update_vip(vserver=vserver, vip=vip, partition=partition)

        # 찾은거 release 하고, addr 로 찾아가서 update
        VIPAddrDao.take_and_release(
            db=db,
            old=VIPAddrDao.find_by_addr(db=db, addr=origin_vip),
            new=VIPAddrDao.find_by_addr(db=db, addr=vip),
        )


class Pool:
    mgmt = None
    pool_obj = None

    def __init__(self, mgmt):
        self.mgmt = mgmt
        self.pool_obj = mgmt.tm.ltm.pools.pool

    def find_or_create(self, pool: PoolModel, params):
        found = self.find(pool)
        params["monitor"] = f"/{pool.partition}/tcp"
        return found if found else self.create(pool=pool, params=params)

    def find(self, pool: PoolModel):
        if not self.pool_obj.exists(name=pool.name, partition=pool.partition):
            return

        return self.pool_obj.load(name=pool.name, partition=pool.partition)

    def create(self, pool: PoolModel, params):
        params["name"] = pool.name
        params["partition"] = pool.partition
        return self.pool_obj.create(**params)

    def delete(self, pool: PoolModel):
        pool_obj = self.find(pool)
        if not pool_obj:
            raise PoolNotFoundException(f"Pool not found: {pool.name}@{pool.partition}")

        pool_obj.delete()

    def add_member(self, pool, member: MemberModel):
        added = pool.members_s.members.create(
            partition=pool.partition, name=member.name
        )
        return added

    def delete_member(self, pool, member: MemberModel):
        if pool.members_s.members.exists(partition=pool.partition, name=member.name):
            m = pool.members_s.members.load(partition=pool.partition, name=member.name)
            m.delete()

    def enable_member(self, pool, member: MemberModel):
        if pool.members_s.members.exists(partition=pool.partition, name=member.name):
            m = pool.members_s.members.load(partition=pool.partition, name=member.name)
            m.session = "user-enabled"
            m.update()

    def disable_member(self, pool, member: MemberModel):
        if pool.members_s.members.exists(partition=pool.partition, name=member.name):
            m = pool.members_s.members.load(partition=pool.partition, name=member.name)
            m.session = "user-disabled"
            m.update()

    def search_by_node_name(self, name: str):
        matched = []
        all_pools = self.mgmt.tm.ltm.pools.get_collection()
        for pool in all_pools:
            members = pool.members_s.get_collection()
            for member in members:
                if re.search(rf"{name}", member.name):
                    matched.append(pool)
                    break

        return matched


class Node:
    mgmt = None
    node_obj = None

    def __init__(self, mgmt):
        self.mgmt = mgmt
        self.node_obj = mgmt.tm.ltm.nodes

    def search_by_name(self, q: str = "k8s"):
        matched = []
        nodes = self.node_obj.get_collection()
        for node in nodes:
            name = node.name
            if re.search(rf"{q}", name):
                matched.append(node)

        return matched

    def find(self, name: str, partition: str):
        if not self.node_obj.node.exists(name=name, partition=partition):
            return

        return self.node_obj.node.load(name=name, partition=partition)

    def create(self, name: str, partition: str, address: str, description: str):
        return self.node_obj.node.create(
            name=name, partition=partition, address=address, description=description
        )

    def delete(self, name: str, partition: str):
        node = self.find(name=name, partition=partition)
        if not node:
            raise NodeNotFoundException(f"Node not found: {name}@{partition}")

        node.delete()


## VirtualServer
class Virtual:
    mgmt = None
    virtual_obj = None

    def __init__(self, mgmt):
        self.mgmt = mgmt
        self.virtual_obj = mgmt.tm.ltm.virtuals.virtual

    def find(self, name: str, partition: str):
        if not self.virtual_obj.exists(name=name, partition=partition):
            return

        return self.virtual_obj.load(name=name, partition=partition)

    def create(self, vserver: VirtualServerModel):
        params = {
            "name": vserver.name,
            "partition": vserver.partition,
            "pool": vserver.pool,
            "sourceAddressTranslation": vserver.sourceAddressTranslation,
            "snatpool": vserver.snatpool,
            "source": vserver.source,
            "mask": vserver.mask,
            "profiles": vserver.profiles,
            "destination": vserver.destination,
        }
        return self.virtual_obj.create(**params)

    def delete(self, name: str, partition: str):
        vserver = self.find(name=name, partition=partition)
        if not vserver:
            raise VServerNotFoundException(
                f"VirtualServer not found: {name}@{partition}"
            )

        vserver.delete()

    ## vserver: <f5.bigip.tm.ltm.virtual.Virtual object at 0x106291050>
    def update_vip(self, vserver, vip: str, partition: str):
        port = vserver.destination.split("/")[-1].split(":")[1]
        destination = f"/{partition}/{vip}:{port}"
        vserver.destination = destination
        vserver.update()


class VIP:
    RESERVED_PRE_HOSTS = 1
    RESERVED_POST_HOSTS = 0

    def create_by_cidr(
        self, db: Session, include_cidr: str, exclude_cidrs: Optional[List[str]] = []
    ):
        ipaddrs = list()
        include_net = ipaddress.IPv4Network(include_cidr)
        for exclude_cidr in exclude_cidrs:
            exclude_net = ipaddress.IPv4Network(exclude_cidr)
            include_net = include_net.address_exclude(exclude_net)

        if isinstance(include_net, ipaddress.IPv4Network):
            for host in include_net.hosts():
                ipaddrs.append(host)
        else:
            for network in list(include_net):
                for host in network.hosts():
                    ipaddrs.append(host)

        ipaddrs.sort()
        ipaddrs = self.__exclude_reserved_hosts(ipaddrs)
        VIPAddrDao.add_all(db=db, ipaddrs=ipaddrs)

    def delete_by_cidr(self, db: Session, cidr: str):
        net = ipaddress.IPv4Network(cidr)
        ipaddrs = [host for host in net.hosts()]
        ipaddrs = self.__exclude_reserved_hosts(ipaddrs)
        VIPAddrDao.delete_all(db=db, ipaddrs=ipaddrs)

    def __exclude_reserved_hosts(
        self, ipaddrs: List[ipaddress.IPv4Address]
    ) -> List[ipaddress.IPv4Address]:
        network_length = len(ipaddrs)
        if network_length <= self.RESERVED_PRE_HOSTS + self.RESERVED_POST_HOSTS:
            raise Exception(
                f"Reserved hosts size are bigger than network: reserved({self.RESERVED_PRE_HOSTS+self.RESERVED_POST_HOSTS}), network({network_length})"
            )

        ipaddrs = ipaddrs[
            self.RESERVED_PRE_HOSTS : network_length - self.RESERVED_POST_HOSTS
        ]
        return ipaddrs
