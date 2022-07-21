from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from ..dao import vipaddr as VIPAddrDao
from ..dependencies import get_db
from ..schemas.vipaddr import VIPAddrSchema, UseYN
from ..models.vipaddr import VIPAddrParams
from ..services.bigip import Bigip, Node, VIP
from ..models.bigip import (
    PoolModel,
    MemberModel,
    VirtualServerModel,
    VirtualServiceModel,
    VirtualServerUpdateParams,
    NodeModel,
    IpPoolModel,
    IpPoolModelDel,
)
from ..errors import (
    PoolNotFoundException,
    VServerNotFoundException,
    VServerNothingToChangeException,
    NodeNotFoundException,
    raise_error,
)

bigip = Bigip()
router = APIRouter(prefix="/bigip", tags=["BIG-IP"])


@router.post("/nodes/")
def create_node(nodeModel: NodeModel):
    name, partition, address, description = (
        nodeModel.name,
        nodeModel.partition,
        nodeModel.address,
        nodeModel.description,
    )
    node = bigip.find_node(name=name, partition=partition)

    if node:
        raise_error(400, f"node already exists: {name}@{partition} {node.address}")

    node = bigip.create_node(
        name=name, address=address, partition=partition, description=description
    )

    if not node:
        raise_error(500, f"Failed to crate a node: {name}@{partition}")

    return {"name": node.name, "address": node.address, "partition": node.partition}


@router.get("/nodes/{name}")
def read_node(name: str, partition: str = "Common"):
    node = bigip.find_node(name=name, partition=partition)
    if not node:
        raise_error(404, f"Node not found: {name}@{partition}")

    pools = bigip.get_pools_by_node_name(name=node.name)

    return {
        "name": node.name,
        "address": node.address,
        "partition": node.partition,
        "pools": {"membership": list(map(lambda pool: pool.name, pools))},
    }


@router.delete("/nodes/{name}")
def delete_node(name: str, partition: str = "Common"):
    try:
        bigip.delete_node(name=name, partition=partition)
    except NodeNotFoundException as error:
        return raise_error(404, f"{error}")
    except Exception as error:
        return raise_error(500, f"{error}")

    return f"Node {name}@{partition} deleted successfully"


@router.delete("/nodes/")
def delete_node(query: str):
    try:
        deleted_names = bigip.delete_nodes(query=query)
        return {
            "nodes": deleted_names,
            "msg": f"Nodes({len(deleted_names)}) deleted successfully by query({query})",
        }
    except Exception as error:
        return raise_error(500, f"{error}")


@router.post("/pools/")
def create_pool(pool: PoolModel, description: Optional[str] = None):
    created = bigip.create_pool(pool=pool, params={"description": description})
    if not created:
        raise_error(500, f"Failed to create a new pool: {pool.name}({pool.partition})")

    return f"{pool.name}({pool.partition}) created"


@router.get("/pools/{name}")
def read_pool(name: str, partition: str = "Common"):
    try:
        pool = bigip.find_pool(pool=PoolModel(name=name, partition=partition))
        members = bigip.get_pool_members(pool=pool)
        pool_members = []
        for member in members:
            pool_members.append({"name": member.name})

        return {"name": pool.name, "members": pool_members}
    except PoolNotFoundException as error:
        return raise_error(404, f"{error}")


@router.patch("/pools/{name}")
def update_pool_members(
    name: str, members: List[MemberModel], partition: str = "Common"
):
    try:
        pool = bigip.find_pool(PoolModel(name=name, partition=partition))
        return bigip.update_pool_members(pool=pool, members=members)
    except PoolNotFoundException as error:
        return raise_error(404, f"{error}")


@router.delete("/pools/{name}")
def delete_pool(name: str, partition: str = "Common"):
    try:
        pool = PoolModel(name=name, partition=partition)
        bigip.delete_pool(pool)
    except PoolNotFoundException as error:

        return raise_error(404, f"{error}")
    except Exception as error:
        return raise_error(500, f"{error}")

    return f"Pool {name}@{partition} deleted successfully"


# member.name = nodeName:port
# e.g. worker-001.k8s-a.wmp.dev:31963
@router.post("/pools/{pool_name}/members/")
def create_pool_members(
    pool_name: str, members: List[MemberModel], partition: str = "Common"
):
    try:
        pool = bigip.find_pool(PoolModel(name=pool_name, partition=partition))
        created = bigip.create_pool_members(pool=pool, members=members)
        return f"Created members({len(created)}) to {pool_name}@{partition}"
    except PoolNotFoundException as error:
        return raise_error(404, f"{error}")
    except Exception as error:
        return raise_error(500, f"{error}")


@router.delete("/pools/{pool_name}/members/")
def delete_pool_members(
    pool_name: str, members: List[MemberModel], partition: str = "Common"
):
    try:
        pool = bigip.find_pool(PoolModel(name=pool_name, partition=partition))
        deleted = bigip.delete_pool_members(pool=pool, members=members)
        return f"Deleted members({len(delete)}) to {pool_name}@{partition}"
    except PoolNotFoundException as error:
        return raise_error(404, f"{error}")
    except Exception as error:
        return raise_error(500, f"{error}")


@router.delete("/pools/{pool_name}/members/{member_name}/")
def delete_pool_member(pool_name: str, member_name: str, partition: str = "Common"):
    try:
        pool = bigip.find_pool(PoolModel(name=pool_name, partition=partition))
        deleted = bigip.delete_pool_member(pool=pool, member=member_name)
        return f"Deleted {member_name} to {pool_name}@{partition}"
    except PoolNotFoundException as error:
        return raise_error(404, f"{error}")
    except Exception as error:
        return raise_error(500, f"{error}")


@router.patch("/pools/{pool_name}/members/{member_name}/")
def session_pool_member(
    pool_name: str,
    member_name: str,
    partition: str = "Common",
    session_enable: str = "true",
):
    try:
        pool = bigip.find_pool(PoolModel(name=pool_name, partition=partition))
        if session_enable == "true":
            enabled = bigip.enable_pool_member(pool=pool, member=member_name)
            return f"enabled {member_name} to {pool_name}@{partition}"
        elif session_enable == "false":
            disabled = bigip.disable_pool_member(pool=pool, member=member_name)
            return f"disabled {member_name} to {pool_name}@{partition}"
    except PoolNotFoundException as error:
        return raise_error(404, f"{error}")
    except Exception as error:
        return raise_error(500, f"{error}")


@router.post("/ippools")
def create_ip_cidr(ippool_model: IpPoolModel, db: Session = Depends(get_db)):
    ip_cidr = ippool_model.ip_cidr
    ip_cidr_exclude = ippool_model.ip_cidr_exclude

    try:
        if ip_cidr.count(".") != 3:
            raise Exception("ValidationError")
        elif ip_cidr.count("/") != 1:
            raise Exception("ValidationError")
        else:
            VIP().create_by_cidr(
                db=db, include_cidr=ip_cidr, exclude_cidrs=ip_cidr_exclude
            )
    except Exception as error:
        return raise_error(500, f"{error}")
    return f"Pool {ip_cidr} created successfully"


@router.delete("/ippools")
def delete_ip_cidr(
    ip_cidr: str = "192.168.30.0/24",
    db: Session = Depends(get_db),
):
    try:
        if ip_cidr.count(".") != 3:
            raise Exception("ValidationError")
        elif ip_cidr.count("/") != 1:
            raise Exception("ValidationError")
        else:
            VIP().delete_by_cidr(db=db, cidr=ip_cidr)
    except Exception as error:
        return raise_error(500, f"{error}")
    return f"Pool {ip_cidr} Deleted successfully"


# hostname: e.g. `dev-api-infracm.wemakeprice.kr`
@router.post("/kubernetes/pools/{hostname}")
def create_kubernetes_pool(
    hostname: str,
    node_name_patterns: List[str] = ["a.wmp.dev", "b.wmp.dev", "gke"],
    partition: str = "Common",
):
    mapped_port = {80: 30633, 443: 31963}
    targets = []

    node = Node(bigip.mgmt)
    for pattern in node_name_patterns:
        targets += node.search_by_name(q=pattern)

    msg = []
    for port in [80, 443]:
        name = f"{hostname}_{port}"
        pool_model = PoolModel(name=name, partition=partition)
        pool = None
        try:
            pool = bigip.find_pool(pool=pool_model)
        except PoolNotFoundException as exception:
            pool = bigip.create_pool(pool=pool_model, params={})
        finally:
            if not pool:
                return raise_error(500, f"Failed to create a new pool: {name}")

        members = []
        for target in targets:
            members.append(MemberModel(name=f"{target.name}:{mapped_port[port]}"))

        try:
            created = bigip.create_pool_members(pool=pool, members=members)
            msg.append(f"Created members({len(created)}) to {name}")
        except Exception as error:
            return raise_error(500, f"{error}")

    return msg


@router.delete("/kubernetes/pools/{hostname}")
def delete_kubernetes_pool(
    hostname: str,
    partition: str = "Common",
):
    """
    BIG-IP 에서 hostname_80, hostname_443 Pool object 를 삭제합니다.
    """
    msg = []
    for port in [80, 443]:
        name = f"{hostname}_{port}"
        msg.append(delete_pool(name=name, partition=partition))

    return msg


@router.delete("/kubernetes/pools/{hostname}/members")
def delete_kubernetes_pool_members(
    hostname: str,
    node_name_patterns: List[str] = ["a.wmp.dev", "b.wmp.dev", "gke"],
    partition: str = "Common",
):
    """
    BIG-IP 의 hostname_80, hostname_443 Pool object 에서 node_name_patterns 에 matching 되는 member 를 제거합니다.
    """
    mapped_port = {80: 30633, 443: 31963}
    targets = []

    node = Node(bigip.mgmt)
    for pattern in node_name_patterns:
        targets += node.search_by_name(q=pattern)

    msg = []
    for port in [80, 443]:
        name = f"{hostname}_{port}"
        pool_model = PoolModel(name=name, partition=partition)
        pool = None
        try:
            pool = bigip.find_pool(pool=pool_model)
        except PoolNotFoundException as error:
            return raise_error(403, f"can not found pool: {name}")
        except Exception as error:
            return raise_error(500, f"{error}")

        members = []
        for target in targets:
            members.append(MemberModel(name=f"{target.name}:{mapped_port[port]}"))

        try:
            deleted = bigip.delete_pool_members(pool=pool, members=members)
            msg.append(f"Deleted members({len(deleted)}) to {name}")
        except Exception as error:
            return raise_error(500, f"{error}")

    return msg


@router.patch("/kubernetes/pools/{hostname}")
def session_kubernetes_pool(
    hostname: str,
    node_name_patterns: List[str] = ["a.wmp.dev", "b.wmp.dev", "gke"],
    partition: str = "Common",
    session_enable: str = "true",
):
    """
    BIG-IP 의 `hostname`_443, `hostname`_80 에 해당하는 pool member 의 status 를 입력된 `session_enable` 로 변경합니다.

    **WARNING** membership 을 변경하는 API 가 아닙니다.
    Pool 의 membership 변경을 위해서는 `PATCH /bigip/pools/:name` API 를 사용합니다.
    """
    mapped_port = {80: 30633, 443: 31963}
    targets = []

    node = Node(bigip.mgmt)
    for pattern in node_name_patterns:
        targets += node.search_by_name(q=pattern)

    for port in [80, 443]:
        name = f"{hostname}_{port}"
        pool_model = PoolModel(name=name, partition=partition)
        pool = None
        try:
            pool = bigip.find_pool(pool=pool_model)
        except PoolNotFoundException as error:
            return raise_error(403, f"can not found pool: {name}")
        except Exception as error:
            return raise_error(500, f"{error}")

        for target in targets:
            member = f"{target.name}:{mapped_port[port]}"
            try:
                if session_enable == "true":
                    enabled = bigip.enable_pool_member(pool=pool, member=member)
                    msg = f"enabled {node_name_patterns} to {hostname}"
                elif session_enable == "false":
                    disabled = bigip.disable_pool_member(pool=pool, member=member)
                    msg = f"disabled {node_name_patterns} to {hostname}"
            except Exception as error:
                return raise_error(500, f"{error}")

    return msg


@router.post("/kubernetes/vserver")
def create_kubernetes_vserver(
    virtual_service: VirtualServiceModel, db: Session = Depends(get_db)
):
    hostname, vip = virtual_service.hostname, virtual_service.vip
    available = (
        VIPAddrDao.find_by_addr(db=db, addr=vip)
        if vip
        else VIPAddrDao.find_by_flag(db=db, use_yn=UseYN.N)
    )
    if not available:
        raise_error(code=500, msg="There are no valid resources")

    vip = available.vip_addr
    ## UseYN enum 을 쓰니까 좀 헛갈리는 듯
    if available.use_yn != UseYN.N.value:
        raise_error(code=400, msg=f"VIP already in use: {vip}")

    msg = []
    snatpool = bigip.configs.bigip_snatpool
    for port in [80, 443]:
        vs_name = f"{hostname}_{port}"
        destination = f"{vip}:{port}"
        vserver_model = VirtualServerModel(
            name=vs_name, pool=vs_name, snatpool=snatpool, destination=destination
        )
        try:
            bigip.create_vserver(vserver=vserver_model)
        except PoolNotFoundException as error:
            return raise_error(
                404, f"pool not found: {vserver_model.pool}@{vserver_model.partition}"
            )
        except Exception as error:
            return raise_error(500, f"create_vserver failed: {error}")
        msg.append(f"{vserver_model.name}@{vip} created")

    VIPAddrDao.update(
        db=db,
        row=available,
        params=VIPAddrParams(vip_addr=vip, domain_name=hostname, use_yn=UseYN.Y),
    )
    return msg


@router.delete("/kubernetes/vserver/{hostname}")
def delete_kubernetes_vserver(
    hostname: str, partition: str = "Common", db: Session = Depends(get_db)
):
    msg = []
    for port in [80, 443]:
        vs_name = f"{hostname}_{port}"
        try:
            bigip.delete_vserver(name=vs_name, partition=partition)
        except VServerNotFoundException as error:
            return raise_error(404, f"{error}")
        except Exception as error:
            return raise_error(500, f"{error}")
        msg.append(f"VirtualServer {hostname}_{port} deleted successfully")

    row = VIPAddrDao.find_by_hostname(db=db, hostname=hostname)
    if not row:
        raise_error(
            code=500,
            msg=f"VirtualServer was deleted successfully({''.join(msg)}), but hostname({hostname}) was not found in vipaddr pool",
        )
    VIPAddrDao.reset(db=db, row=row)
    return msg


@router.patch("/kubernetes/vserver/{hostname}")
def update_kubernetes_vserver(
    hostname: str, params: VirtualServerUpdateParams, db: Session = Depends(get_db)
):
    vip, partition = params.vip, params.partition

    try:
        bigip.update_vserver_vip(hostname=hostname, vip=vip, db=db, partition=partition)
    except VServerNotFoundException as error:
        return raise_error(404, f"{error}")
    except VServerNothingToChangeException as error:
        return raise_error(400, f"{error}")
    except Exception as error:
        return raise_error(500, f"{error}")

    return f"{hostname}@{partition} VirtualServers vip updated to {vip} successfully"


@router.get("/vserver/{name}")
def read_vserver(name: str, partition: str = "Common"):
    vserver = bigip.find_vserver(name=name, partition=partition)
    if not vserver:
        return raise_error(404, f"VirtualServer not found: {name}@{partition}")

    destination = vserver.destination
    vip = destination.split("/")[-1].split(":")[0]
    return {"name": vserver.name, "address": vip}


@router.post("/vserver/")
def create_vserver(vserver: VirtualServerModel):
    try:
        created = bigip.create_vserver(vserver=vserver)
        if not created:
            raise_error(
                500,
                f"Failed to create a new VirtualServer: {vserver.name}@{vserver.partition}",
            )
    except PoolNotFoundException as error:
        return raise_error(404, f"pool not found: {vserver.pool}@{vserver.partition}")
    except Exception as error:
        return raise_error(500, f"create_vserver failed: {error}")

    return f"{vserver.name}@{vserver.partition} created"


@router.delete("/vserver/{name}")
def delete_vserver(name: str, partition: str = "Common"):
    try:
        bigip.delete_vserver(name=name, partition=partition)
    except VServerNotFoundException as error:
        return raise_error(404, f"{error}")
    except Exception as error:
        return raise_error(500, f"{error}")

    return f"VirtualServer {name}@{partition} deleted successfully"
