from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import logging, os, asyncio, aiomysql, traceback, locale, json
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
    kb = [["temperatura"],["turbidez"],["gráfico temperatura"],["gráfico turbidez"], ["alimentar"],["estado"]]
    await context.bot.send_message(update.message.chat.id, text="Bienvenido al Bot "+ nombre + " " + apellido,reply_markup=ReplyKeyboardMarkup(kb))

async def acercade(update: Update, context):
    await context.bot.send_message(update.message.chat.id, text="Este bot fue creado para recibirme xd")
        
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
            unidad = ' MTU'
        await context.bot.send_message(update.message.chat.id,
                                    text="La última {} es de {} {},\nregistrada a las {:%H:%M:%S %d/%m/%Y}"
                                    .format(update.message.text, str(r[1]).replace('.',','), unidad, r[0]))
        logging.info("La última {} es de {} {}, medida a las {:%H:%M:%S %d/%m/%Y}".format(update.message.text, r[1], unidad, r[0]))
    conn.close()

async def graficos(update: Update, context):
    logging.info(update.message.text)
    sql = f"SELECT timestamp, {update.message.text.split()[1]} FROM mediciones where id mod 2 = 0 AND timestamp >= NOW() - INTERVAL 2 DAY ORDER BY timestamp"
    conn = await aiomysql.connect(host=os.environ["MARIADB_SERVER"], port=3306,
                                    user=os.environ["MARIADB_USER"],
                                    password=os.environ["MARIADB_USER_PASS"],
                                    db=os.environ["MARIADB_DB"])
    async with conn.cursor() as cur:
        await cur.execute(sql)
        filas = await cur.fetchall()

        fig, ax = plt.subplots(figsize=(7, 4))
        fecha,var=zip(*filas)
        ax.plot(fecha,var)
        ax.grid(True, which='both')
        ax.set_title(update.message.text, fontsize=14, verticalalignment='bottom')
        ax.set_xlabel('fecha')
        ax.set_ylabel('unidad')

        buffer = BytesIO()
        fig.tight_layout()
        fig.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=buffer)
        buffer.close()
    conn.close()

#ACA ARRANCAN LOS ACTUADORES DEL BOT
async def setpoint_temperatura(update: Update, context):
    logging.info(update.message.text)
    async with aiomqtt.Client(
        os.environ["SERVIDOR"],
        port=1883,
    ) as client:
        topico = update.message.text.split()[0]
        topico=topico[1:]
        try:
            if float(context.args[0]) > 0.0 and float(context.args[0]) < 40.0:
                await client.publish(topic=topico, payload=context.args[0] , qos=1)
                await context.bot.send_message(update.message.chat.id, text="Valor de temperatura seteado en {}".format(context.args[0]))
            else:
                await context.bot.send_message(update.message.chat.id, text="Ingrese un valor correcto de seteo de temperatura")
        except ValueError:
            await context.bot.send_message(update.message.chat.id, text="Ingrese un valor correcto de seteo de temperatura")

async def setpoint_turbidez(update: Update, context):
    logging.info(update.message.text)
    async with aiomqtt.Client(
        os.environ["SERVIDOR"],
        port=1883,
    ) as client:
        topico = update.message.text.split()[0]
        topico=topico[1:]
        try:
            if float(context.args[0]) > 0.0 and float(context.args[0]) < 3000.0:
                await client.publish(topic=topico, payload=context.args[0] , qos=1)
                await context.bot.send_message(update.message.chat.id, text="Valor de turbidez seteado en {}".format(context.args[0]))
            else:
                await context.bot.send_message(update.message.chat.id, text="Ingrese un valor correcto de seteo de turbidez")
        except ValueError:
            await context.bot.send_message(update.message.chat.id, text="Ingrese un valor correcto de seteo de turbidez")

async def modo(update: Update, context):
    logging.info(context.args)
    async with aiomqtt.Client(
        os.environ["SERVIDOR"],
        port=1883,
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
    async with aiomqtt.Client(
        os.environ["SERVIDOR"],
        port=1883,
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

async def alimentar(update: Update, context):
    logging.info(update.message.text)
    async with aiomqtt.Client(
        os.environ["SERVIDOR"],
        port=1883,
    ) as client:
        topico = update.message.text
        try:
            await client.publish(topic=topico, payload=1, qos=1) #envía un 1, el esp activa el destello
            await context.bot.send_message(update.message.chat.id, text="Alimentando")
        except ValueError:
            await context.bot.send_message(update.message.chat.id, text="No se pudo alimentar")

'''
async def estado(update: Update, context):
    logging.info(update.message.text)
    async with aiomqtt.Client(
        os.environ["SERVIDOR"],
        port=1883,
    ) as client:
        topico = update.message.text
        try:
            await client.publish(topic=topico, payload=1, qos=1) #envía un 1, el esp activa el destello
            await context.bot.send_message(update.message.chat.id, text="Consultando estado")
            await client.subscribe("estados/#")  # CLIENT_ID debe estar en tus env vars
            async for message in messages:
                try:
                    data = json.loads(message.payload.decode())
                    texto = (
                        f"Estado de actuadores:\n"
                        f"Calentador: {'Encendido' if data['calentador'] else 'Apagado'}\n"
                        f"Ventilador: {'Encendido' if data['ventilador'] else 'Apagado'}\n"
                        f"Filtro: {'Encendido' if data['filtro'] else 'Apagado'}"
                    )
                    await context.bot.send_message(update.message.chat.id, text=texto)
                except Exception as e:
                    logging.error("Error procesando estado: %s", e)
                    await context.bot.send_message(update.message.chat.id, text="Error procesando la respuesta de estado")
        except ValueError:
            await context.bot.send_message(update.message.chat.id, text="No se pudo verificar el estado")
'''
import asyncio

async def estado(update, context):
    logging.info(update.message.text)

    try:
        async with aiomqtt.Client(
            os.environ["SERVIDOR"],
            port=1883,
        ) as client:

            async with client.messages() as messages:
                # suscribirse antes de publicar
                await client.subscribe("estados/#")
                logging.info("Suscripto a estados/#")

                # publicar la petición
                await client.publish(topic="estado", payload=1, qos=1)
                await context.bot.send_message(update.message.chat.id, text="Consultando estado...")

                try:
                    # esperar respuesta con timeout
                    message = await asyncio.wait_for(messages.__anext__(), timeout=5.0)
                    logging.info("Mensaje recibido: %s", message.payload.decode())

                    data = json.loads(message.payload.decode())
                    texto = (
                        f"Estado de actuadores:\n"
                        f"🔥 Calentador: {'Encendido' if data['calentador'] else 'Apagado'}\n"
                        f"💨 Ventilador: {'Encendido' if data['ventilador'] else 'Apagado'}\n"
                        f"💧 Filtro: {'Encendido' if data['filtro'] else 'Apagado'}"
                    )
                    await context.bot.send_message(update.message.chat.id, text=texto)

                except asyncio.TimeoutError:
                    await context.bot.send_message(update.message.chat.id, text="No se recibió respuesta del ESP32 en 5 segundos.")

    except Exception as e:
        logging.error("Error en estado: %s", e)
        await context.bot.send_message(update.message.chat.id, text="Error al verificar estado")


async def ventilador(update: Update, context):
    logging.info(context.args)
    async with aiomqtt.Client(
        os.environ["SERVIDOR"],
        port=1883,
    ) as client:
        topico = update.message.text.split()[0]
        topico=topico[1:]
        try:
            if context.args and (context.args[0] == 'encendido' or context.args[0] == 'apagado'):
                await client.publish(topic=topico, payload=context.args[0] , qos=1)
                await context.bot.send_message(update.message.chat.id, text="Estado ventilador: {}".format(context.args[0]))
            else:
                await context.bot.send_message(update.message.chat.id, text="Ingrese un estado de ventilador válido")
        except ValueError:
            await context.bot.send_message(update.message.chat.id, text="Ingrese un estado de ventilador valido")

async def calentador(update: Update, context):
    logging.info(context.args)
    async with aiomqtt.Client(
        os.environ["SERVIDOR"],
        port=1883,
    ) as client:
        topico = update.message.text.split()[0]
        topico=topico[1:]
        try:
            if context.args and (context.args[0] == 'encendido' or context.args[0] == 'apagado'):
                await client.publish(topic=topico, payload=context.args[0] , qos=1)
                await context.bot.send_message(update.message.chat.id, text="Estado calentador: {}".format(context.args[0]))
            else:
                await context.bot.send_message(update.message.chat.id, text="Ingrese un estado de calentador válido")
        except ValueError:
            await context.bot.send_message(update.message.chat.id, text="Ingrese un estado de calentador valido")

async def filtro(update: Update, context):
    logging.info(context.args)
    async with aiomqtt.Client(
        os.environ["SERVIDOR"],
        port=1883,
    ) as client:
        topico = update.message.text.split()[0]
        topico=topico[1:]
        try:
            if context.args and (context.args[0] == 'encendido' or context.args[0] == 'apagado'):
                await client.publish(topic=topico, payload=context.args[0] , qos=1)
                await context.bot.send_message(update.message.chat.id, text="Estado filtro: {}".format(context.args[0]))
            else:
                await context.bot.send_message(update.message.chat.id, text="Ingrese un estado de filtro válido")
        except ValueError:
            await context.bot.send_message(update.message.chat.id, text="Ingrese un estado de filtro valido")

def main():
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('acercade', acercade))
    application.add_handler(MessageHandler(filters.Regex("^(temperatura|turbidez)$"), medicion))
    application.add_handler(MessageHandler(filters.Regex("^(gráfico temperatura|gráfico turbidez)$"), graficos))

    application.add_handler(CommandHandler('setpointtemperatura', setpoint_temperatura))
    application.add_handler(CommandHandler('setpointturbidez', setpoint_turbidez))
    application.add_handler(CommandHandler('modo', modo))
    application.add_handler(CommandHandler('periodo', periodo))
    application.add_handler(CommandHandler('ventilador', ventilador))
    application.add_handler(CommandHandler('calentador', calentador))
    application.add_handler(CommandHandler('filtro', filtro))
    application.add_handler(MessageHandler(filters.Regex("^(alimentar)$"), alimentar))
    application.add_handler(MessageHandler(filters.Regex("^(estado)$"), estado))
    application.run_polling()

if __name__ == '__main__':
    main()
