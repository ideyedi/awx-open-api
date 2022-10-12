### AWX Crawler
**Abstarct**  
Docker based AWX 드롭다운 보이지 않는 문제로 인해 웹 크롤러를 이용  
Inventory source를 생성하는 걸 목적으로 한다.
---
**Environment**  
Python 3.8.12  
Python virtual : pipenv

example  
1. python 3.8.12 설치해야합니다.
> python --version  
> Python 3.8.12  

2. pipenv 구성
> pip install pipenv

3. 가상환경 생성 (처음 생성할 경우 자동으로 실행됩니다.)
> pipenv --python 3.8.12  

- 가상환경 실행, 종료  
> pipenv shell  
> exit

4. 가상환경에 패키지 설치
> pipenv sync  
> pip list

5. 크롤러 실행
> python make_inven.py