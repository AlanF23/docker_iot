import asyncio, ssl, certifi, logging, os
import aiomqtt

logging.basicConfig(format='%(asctime)s - cliente mqtt - %(levelname)s:%(message)s', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S %z')

async def topico1():
    global topicos
    while True:
        menssage = await topicos
        logging.info(str(message.topic) + ": " + message.payload.decode("utf-8"))
        await asyncio.sleep(5)

async def recibir(client):
    global topicos
    while True:
        async for message in client.messages:
            if message.topic == os.environ['TOPICO1']:
                topicos.apend(menssage.topic)

async def publicar(client):
    while True:
        await client.publish(os.environ['TOPICO3'], "publicando", qos=1)
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
        task_1=asyncio.create_task(topico1(),name='task1')
        task_2=asyncio.create_task(publicar(client),name='task2')
        task_3=asyncio.create_task(recibir(client),name='task3')
        #async for message in client.messages:
        #    logging.info(str(message.topic) + ": " + message.payload.decode("utf-8"))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)