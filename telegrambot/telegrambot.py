from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import logging, os, asyncio, aiomysql, traceback, locale, ssl, certifi, json
import matplotlib.pyplot as plt
from io import BytesIO
import aiomqtt
import datetime
import time

token=os.environ["TB_TOKEN"]

logging.basicConfig(format='%(asctime)s - TelegramBot - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("se conectó: " + str(update.message.from_user.id))
    if update.message.from_user.first_name:
        nombre=update.message.from_user.first_name
    else:
        nombre=""
    if update.message.from_user.last_name:
        apellido=update.message.from_user.last_name
    else:
        apellido=""
    kb = [["temperatura"],["humedad"],["gráfico temperatura"],["gráfico humedad"], ["destello"]]
    await context.bot.send_message(update.message.chat.id, text="Bienvenido al Bot "+ nombre + " " + apellido,reply_markup=ReplyKeyboardMarkup(kb))

async def acercade(update: Update, context):
    await context.bot.send_message(update.message.chat.id, text="Este bot fue creado por AlanF23 para el curso de IoT FIO")
'''
async def kill(update: Update, context):
    logging.info(context.args)
    if context.args and context.args[0] == '@e':
        await context.bot.send_animation(update.message.chat.id, "CgACAgQAAxkBAAMJZk-RMAb2CuP8LWR5bnrFExFGpgwAAh8DAALJ4axTw0mii4VDh981BA")
        await asyncio.sleep(6)
        await context.bot.send_message(update.message.chat.id, text="¡¡¡Ahora estan todos muertos!!!")
    else:
        await context.bot.send_message(update.message.chat.id, text="☠️ ¡¡¡Esto es muy peligroso!!! ☠️")'''
        
async def medicion(update: Update, context):
    logging.info(update.message.text)
    sql = f"SELECT timestamp, {update.message.text} FROM mediciones ORDER BY timestamp DESC LIMIT 1"
    conn = await aiomysql.connect(host=os.environ["MARIADB_SERVER"], port=3306,
                                    user=os.environ["MARIADB_USER"],
                                    password=os.environ["MARIADB_USER_PASS"],
                                    db=os.environ["MARIADB_DB"])
    async with conn.cursor() as cur:
        await cur.execute(sql)
        r = await cur.fetchone()
        if update.message.text == 'temperatura':
            unidad = 'ºC'
        else:
            unidad = '%'
        await context.bot.send_message(update.message.chat.id,
                                    text="La última {} es de {} {},\nregistrada a las {:%H:%M:%S %d/%m/%Y}"
                                    .format(update.message.text, str(r[1]).replace('.',','), unidad, r[0]))
        logging.info("La última {} es de {} {}, medida a las {:%H:%M:%S %d/%m/%Y}".format(update.message.text, r[1], unidad, r[0]))
    conn.close()

async def graficos(update: Update, context):
    logging.info(update.message.text)
    # Construir la consulta SQL de manera segura
    parametro = update.message.text.split()[1]
    sql = f"SELECT timestamp, {parametro} FROM mediciones WHERE id % 2 = 0 AND timestamp >= NOW() - INTERVAL 1 DAY ORDER BY timestamp"
    try:
        # Conectarse a la base de datos
        conn = await aiomysql.connect(
            host=os.environ["MARIADB_SERVER"], 
            port=3306,
            user=os.environ["MARIADB_USER"],
            password=os.environ["MARIADB_USER_PASS"],
            db=os.environ["MARIADB_DB"]
        )

        async with conn.cursor() as cur:
            await cur.execute(sql)
            filas = await cur.fetchall()

            if not filas:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="No se encontraron datos para el gráfico.")
                return

            # Desempaquetar los resultados
            fecha, var = zip(*filas)

            # Crear el gráfico
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.plot(fecha, var)
            ax.grid(True, which='both')
            ax.set_title(update.message.text, fontsize=14, verticalalignment='bottom')
            ax.set_xlabel('Fecha')
            ax.set_ylabel('Unidad')

            # Guardar el gráfico en un buffer
            buffer = BytesIO()
            fig.tight_layout()
            fig.savefig(buffer, format='png')
            buffer.seek(0)

            # Enviar el gráfico
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=buffer)

    except Exception as e:
        logging.error(f"Error al generar el gráfico: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Ocurrió un error al generar el gráfico.")
    
    finally:
        if conn:
            conn.close()

#ACA EMPIEZA LO NUEVO

async def setpoint(update: Update, context):
    logging.info(update.message.text)
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True
    tls_context.load_default_certs()
    async with aiomqtt.Client(
        os.environ["SERVIDOR"],
        username=os.environ["MQTT_USR"],
        password=os.environ["MQTT_PASS"],
        port=int(os.environ["PUERTO_MQTTS"]),
        tls_context=tls_context,
    ) as client:
        topico = update.message.text.split()[0]
        topico=topico[1:]
        try:
            if float(context.args[0]) > 0.0 and float(context.args[0]) < 60.0:
                await client.publish(topic=topico, payload=context.args[0] , qos=1)
                await context.bot.send_message(update.message.chat.id, text="Valor de temperatura seteado en {}".format(context.args[0]))
            else:
                await context.bot.send_message(update.message.chat.id, text="Ingrese un valor correcto de seteo")
        except ValueError:
            await context.bot.send_message(update.message.chat.id, text="Ingrese un valor correcto de seteo")

async def modo(update: Update, context):
    logging.info(context.args)
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True
    tls_context.load_default_certs()
    async with aiomqtt.Client(
        os.environ["SERVIDOR"],
        username=os.environ["MQTT_USR"],
        password=os.environ["MQTT_PASS"],
        port=int(os.environ["PUERTO_MQTTS"]),
        tls_context=tls_context,
    ) as client:
        topico = update.message.text.split()[0]
        topico=topico[1:]
        try:
            if context.args and (context.args[0] == 'auto' or context.args[0] == 'manual'):
                await client.publish(topic=topico, payload=context.args[0] , qos=1)
                await context.bot.send_message(update.message.chat.id, text="Modo actual: {}".format(context.args[0]))
            else:
                await context.bot.send_message(update.message.chat.id, text="Ingrese un modo válido")
        except ValueError:
            await context.bot.send_message(update.message.chat.id, text="Ingrese un modo valido")

async def periodo(update: Update, context):
    logging.info(context.args)
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True
    tls_context.load_default_certs()
    async with aiomqtt.Client(
        os.environ["SERVIDOR"],
        username=os.environ["MQTT_USR"],
        password=os.environ["MQTT_PASS"],
        port=int(os.environ["PUERTO_MQTTS"]),
        tls_context=tls_context,
    ) as client:
        topico = update.message.text.split()[0]
        topico=topico[1:]
        try:
            if float(context.args[0]) > 0.0 and float(context.args[0]) < 60.0:
                await client.publish(topic=topico, payload=context.args[0] , qos=1)
                await context.bot.send_message(update.message.chat.id, text="Periodo seteado en {} segundos".format(context.args[0]))
            else:
                await context.bot.send_message(update.message.chat.id, text="Ingrese un valor correcto de periodo")
        except ValueError:
            await context.bot.send_message(update.message.chat.id, text="Ingrese un valor correcto de periodo")

async def destello(update: Update, context):
    logging.info(update.message.text)
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True
    tls_context.load_default_certs()
    async with aiomqtt.Client(
        os.environ["SERVIDOR"],
        username=os.environ["MQTT_USR"],
        password=os.environ["MQTT_PASS"],
        port=int(os.environ["PUERTO_MQTTS"]),
        tls_context=tls_context,
    ) as client:
        topico = update.message.text
        try:
            await client.publish(topic=topico, payload=1, qos=1) #envía un 1, el esp activa el destello
            await context.bot.send_message(update.message.chat.id, text="Destellando")
        except ValueError:
            await context.bot.send_message(update.message.chat.id, text="No se pudo destellar")

async def rele(update: Update, context):
    logging.info(context.args)
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True
    tls_context.load_default_certs()
    async with aiomqtt.Client(
        os.environ["SERVIDOR"],
        username=os.environ["MQTT_USR"],
        password=os.environ["MQTT_PASS"],
        port=int(os.environ["PUERTO_MQTTS"]),
        tls_context=tls_context,
    ) as client:
        topico = update.message.text.split()[0]
        topico=topico[1:]
        try:
            if context.args and (context.args[0] == 'encendido' or context.args[0] == 'apagado'):
                await client.publish(topic=topico, payload=context.args[0] , qos=1)
                await context.bot.send_message(update.message.chat.id, text="Estado relé: {}".format(context.args[0]))
            else:
                await context.bot.send_message(update.message.chat.id, text="Ingrese un estado de relé válido")
        except ValueError:
            await context.bot.send_message(update.message.chat.id, text="Ingrese un estado de relé valido")

def main():
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('acercade', acercade))
    application.add_handler(MessageHandler(filters.Regex("^(temperatura|humedad)$"), medicion))
    application.add_handler(MessageHandler(filters.Regex("^(gráfico temperatura|gráfico humedad)$"), graficos))

    #aca empieza lo mio
    application.add_handler(CommandHandler('setpoint', setpoint))
    application.add_handler(CommandHandler('modo', modo))
    application.add_handler(CommandHandler('periodo', periodo))
    application.add_handler(CommandHandler('rele', rele))
    application.add_handler(MessageHandler(filters.Regex("^(destello)$"), destello))
    application.run_polling()

if __name__ == '__main__':
    main()
