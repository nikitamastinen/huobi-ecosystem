import asyncio
import json
import time
from contextlib import redirect_stdout
from typing import List
import aioconsole
import asyncssh

from fetch_balance import get_balance, get_usdt_balance

asyncssh.known_hosts = None
start_bots = False


with open("data.json", "r") as servers:
    data = json.load(servers)


def validate_servers():
    for i in data:
        i['BASE_CURRENCY'] = int(float(get_usdt_balance(
            API_KEY=i['API_KEY'],
            API_SECRET=i['API_SECRET'],
            ACCOUNT_ID=i['SPOT_ID']
        )))
    with open("data.json", "w") as dmp:
        json.dump(data, dmp, indent=2)


async def run_client(index) -> List[asyncssh.SSHCompletedProcess]:
    print(index)
    async with asyncssh.connect(
            data[index]["IP"],
            password=data[index]["PASSWORD"],
            username=data[index]["USERNAME"],
            known_hosts=None
    ) as conn:
        result = [await conn.run('''
        sudo rm -rf .huobi
        mkdir -p .huobi
        ''')]
        print(f"CONNECTED {index}")
        async with conn.start_sftp_client() as sftp:
            await sftp.put('bot_control.py', './.huobi')
            await sftp.put('main.py', './.huobi')
            await sftp.put('telegram_control.py', './.huobi')
            await sftp.put('state.py', './.huobi')
            await sftp.put('requirements.txt', './.huobi')
            await sftp.put('__init__.py', './.huobi')
            await sftp.put('_constants.py', './.huobi')
        print(f'TRANSFER SUCCESS {index}')

        result += [await conn.run('''
            sudo apt update
            sudo apt install -y python3-pip
            sudo apt install -y python3-venv
            cd .huobi
            python3 -m venv venv
            venv/bin/python -m pip install --upgrade pip
            venv/bin/pip install -r requirements.txt
        ''')]
        print(f'DEPLOY SUCCESS {index}')

        # global start_bots
        # while not start_bots:
        #     await asyncio.sleep(0.01)

        # print(f"STARTED BOT {index}")
        try:
            result += [await conn.run(f'''
                        cd .huobi
                        venv/bin/python main.py \
                        {str(index)} \
                        {data[index]["API_KEY"]} \
                        {data[index]["API_SECRET"]} \
                        {data[index]["ACCOUNT_ID"]} \
                        {data[index]["SPOT_ID"]} \
                        {data[index]["INTERVAL"]} \
                        {data[index]["TG_BOT_KEY"]} \
                        {data[index]["BASE_CURRENCY"]} > logs{index}.txt
                    ''')]
            print(result[-1])
            print(f"STARTED BOT {index}")
        except Exception as e:
            print(e)
            pass
        return result


async def run_signal():
    line = await aioconsole.ainput('Press s to start bots...\n')
    if line == 's' or line == 'S':
        global start_bots
        start_bots = True

    return []


async def run_multiple_clients() -> None:
    tasks = (run_client(i) for i in range(len(data)))
    results = await asyncio.gather(*tasks, run_signal(), return_exceptions=True)
    cnt = 0
    for i in results:
        if i:
            cnt += 1
        for result in i:
            with open(f'logs/{cnt}.txt', 'a') as fd:
                with redirect_stdout(fd):
                    print(cnt)
                    print(f'BOT-{cnt} logs\n')
                    if isinstance(result, Exception):
                        print(f'BOT-{cnt}-FAIL: {result}')
                    elif result.exit_status != 0:
                        print(f'BOT-{cnt}-ERR', result.stderr, end='')
                    else:
                        print(f'BOT-{cnt}', result.stdout, end='')

# validate_servers()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(run_multiple_clients())
