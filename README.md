# 달러원 환율

달러원 환율이 바뀌면 알려주는 텔레그램 채널

## 사용법

[달러원 환율](https://t.me/s/dwexr)

## 배포

시간대 설정

```bash
sudo dpkg-reconfigure tzdata
```

패키지 설치

```bash
sudo apt update && sudo apt upgrade -y
```

```bash
sudo apt install python3-pip -y
```

```bash
git clone https://github.com/yehwankim23/dollar-won-exchange-rate.git
```

```bash
pip3 install -r requirements.txt --upgrade
```

실행

```bash
vim main.py
```

```bash
nohup python3 main.py > output.log &
```
