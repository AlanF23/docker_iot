import asyncio, logging, os
import aiomqtt

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S'
)

async def main():
    servidor = os.environ.get("SERVIDOR")
    topico = os.environ.get("TOPICO")

    logging.info(f"Conectando a broker MQTT: {servidor}")
    logging.info(f"Suscribiéndose al tópico: {topico}")

    async with aiomqtt.Client(servidor) as client:
        await client.subscribe(topico)
        logging.info("Suscripción exitosa. Esperando mensajes...")
        
        async for message in client.messages:
            logging.info(f"Mensaje recibido en {message.topic}: {message.payload.decode()}")

if __name__ == "__main__":
    asyncio.run(main())



