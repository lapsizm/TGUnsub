import yaml
import pandas as pd
from telethon import TelegramClient
from telethon.errors import UserNotParticipantError, ChannelInvalidError
from telethon.tl.functions.channels import GetParticipantRequest, EditBannedRequest
from telethon.tl.types import ChatBannedRights
import asyncio

async def _get_chat_id(client, chat_name):
    async for dialog in client.iter_dialogs():
        if dialog.name == chat_name:
            return dialog.id

    print(
        f"Chat with the name {chat_name} was not found in the list of conversations, it will be skipped"
    )
    return None

# Функция для чтения конфигурационного файла
def read_config(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


# Функция для чтения никнеймов из Excel-файла
def read_nicknames(file_path):
    df = pd.read_excel(file_path)
    return df.iloc[:, 0].tolist()


# Читаем конфигурацию
config = read_config('config.yaml')
api_id = config['api_id']
api_hash = config['api_hash']
channel_name = config['telegram_channel_name']
nicknames_file = config['input_nicknames_file']

# Создаем клиент Telegram
client = TelegramClient('account_session', api_id, api_hash)


async def main():
    await client.start()

    # Получаем информацию о канале для проверки корректности имени
    channel = await _get_chat_id(client, channel_name)
    print(channel, channel_name)
    if channel == None:
        return

    # Читаем никнеймы из файла
    nicknames = read_nicknames(nicknames_file)

    # Открываем файл для записи забаненных никнеймов
    with open('bans.txt', 'a') as bans_file:
        for nickname in nicknames:
            try:
                # Получаем информацию о пользователе
                participant = await client(GetParticipantRequest(channel, nickname))

                # Указываем параметры бана (все права запрещены)
                banned_rights = ChatBannedRights(
                    until_date=None,
                    view_messages=True,
                    send_messages=True,
                    send_media=True,
                    send_stickers=True,
                    send_gifs=True,
                    send_games=True,
                    send_inline=True,
                    embed_links=True
                )

                # Баним пользователя
                await client(EditBannedRequest(channel, participant.participant.user_id, banned_rights))
                print(f'Пользователь {nickname} забанен.')

                # Записываем забаненный никнейм в файл
                bans_file.write(f'{nickname}\n')

            except UserNotParticipantError:
                print(f'Пользователь {nickname} не является подписчиком канала.')
            except ChannelInvalidError:
                print(f'Канал с именем {channel_name} не найден или к нему нет доступа.')
                break
            except Exception as e:
                print(f'Произошла ошибка при обработке пользователя {nickname}: {e}')

            await asyncio.sleep(5)


with client:
    client.loop.run_until_complete(main())
