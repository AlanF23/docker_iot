import asyncio, ssl, certifi, logging, os
import aiomqtt

logging.basicConfig(format='%(taskName)s: %(asctime)s - cliente mqtt - %(levelname)s:%(message)s', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S %z')

class contador:
    def __init__(self):
        self.cont = 0
    
    def suma(self):
        self.cont += 1

async def topico1(client):
    while True:
        async for message in client.messages:
            if message.topic == os.environ['TOPICO1']:
                logging.info(str(message.topic) + ": " + message.payload.decode("utf-8"))

async def topico2(client):
    while True:
        async for message in client.messages:
            if message.topic == os.environ['TOPICO2']:
                logging.info(str(message.topic) + ": " + message.payload.decode("utf-8"))

async def contar():
    while True:
        Contador.suma()
        await asyncio.sleep(3)

async def publicar_contador(client):
    while True:
        await client.publish(os.environ['TOPICO3'], Contador.cont, qos=1)
        logging.info(os.environ['TOPICO3'] + ": " + Contador.cont)
        await asyncio.sleep(5)

async def main():
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True
    tls_context.load_default_certs()

    async with aiomqtt.Client(
        os.environ['SERVIDOR'],
        port=8883,
        tls_context=tls_context,
    ) as client:
        await client.subscribe(os.environ['TOPICO1'])
        await client.subscribe(os.environ['TOPICO2'])
        await client.subscribe(os.environ['TOPICO3'])
        task_1=asyncio.create_task(topico1(client),name='topico1')
        task_2=asyncio.create_task(topico1(client),name='topico2')
        task_3=asyncio.create_task(publicar_contador(client),name='contador')

Contador = contador()
        
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)