import asyncio, ssl, certifi, logging, os, aiomysql, json, traceback
from asyncio_mqtt import Client, ProtocolVersion

logging.basicConfig(format='%(asctime)s - cliente mqtt - %(levelname)s:%(message)s', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S %z')

async def main():
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.minimum_version = ssl.TLSVersion.TLSv1_2
    tls_context.maximum_version = ssl.TLSVersion.TLSv1_3
    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True
    tls_context.load_default_certs()


    async with Client(
        os.getenv("SERVIDOR"),
        username=os.getenv("MQTT_USR"),
        password=os.getenv("MQTT_PASS"),
        protocol=ProtocolVersion.V31,
        port=8883,
        tls_context=tls_context,
    ) as client:
        async with client.messages() as messages:
            await client.subscribe('#')
            async for message in messages:
                logging.info(str(message.topic) + ": " + message.payload.decode("utf-8"))
                datos=json.loads(message.payload.decode('utf8'))
                sql = "INSERT INTO `mediciones` (`sensor_id`, `temperatura`, `humedad`) VALUES (%s, %s, %s)"
                try:
                    conn = await aiomysql.connect(host=os.getenv("MARIADB_SERVER"), port=3306,
                                                user=os.getenv("MARIADB_USER"),
                                                password=os.getenv("MARIADB_USER_PASS"),
                                                db=os.getenv("MARIADB_DB"))
                except Exception as e:
                    logging.error(traceback.format_exc())

                cur = await conn.cursor()

                async with conn.cursor() as cur:
                    try:
                        await cur.execute(sql, (message.topic, datos['temperatura'], datos['humedad']))
                    except Exception as e:
                        logging.error(traceback.format_exc())
                        # Logs the error appropriately. 
                    await conn.commit()

                conn.close()


if __name__ == "__main__":
    asyncio.run(main())
