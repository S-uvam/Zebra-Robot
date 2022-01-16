import html
import os
import json
import importlib
import time
import re
import sys
import traceback
import EmikoRobot.modules.sql.users_sql as sql
from sys import argv
from typing import Optional
from telegram import __version__ as peler
from platform import python_version as memek
from EmikoRobot import (
    ALLOW_EXCL,
    CERT_PATH,
    DONATION_LINK,
    LOGGER,
    OWNER_ID,
    PORT,
    SUPPORT_CHAT,
    TOKEN,
    URL,
    WEBHOOK,
    SUPPORT_CHAT,
    dispatcher,
    StartTime,
    telethn,
    pbot,
    updater,
)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from EmikoRobot.modules import ALL_MODULES
from EmikoRobot.modules.helper_funcs.chat_status import is_user_admin
from EmikoRobot.modules.helper_funcs.misc import paginate_modules
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Unauthorized,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.ext.dispatcher import DispatcherHandlerStop, run_async
from telegram.utils.helpers import escape_markdown


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time


PM_START_TEXT = """
*Hello {} !*
✪ ɪ'ᴍ ᴀɴ ᴀɴɪᴍᴇ-ᴛʜᴇᴍᴇ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ ʙᴏᴛ [✨](https://telegra.ph/file/4f0e3eaffec2656e1986e.jpg)
────────────────────────
× *ᴜᴘᴛɪᴍᴇ:* `{}`
× `{}` *ᴜsᴇʀs, ᴀᴄʀᴏss* `{}` *ᴄʜᴀᴛs.*
────────────────────────
✪ ʜɪᴛ /help ᴛᴏ sᴇᴇ ᴍʏ ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴᴅs.
"""

buttons = [
    [
        InlineKeyboardButton(text="ᴀʙᴏᴜᴛ 🆉ᴇʙʀᴀ 🆁ᴏʙᴏᴛ", callback_data="emiko_"),
    ],
    [
        InlineKeyboardButton(text="ʜᴇʟᴘ ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅs", callback_data="help_back"),
        InlineKeyboardButton(
            text="ᴏᴡɴᴇʀ", url="t.me/Simple_Mundaa"
        ),
    ],
    [
        InlineKeyboardButton(
            text="ᴀᴅᴅ 🆉ᴇʙʀᴀ 🆁ᴏʙᴏᴛ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ", url="t.me/Zebra_Ro_bot?startgroup=new"),
    ],
]


HELP_STRINGS = """
Click ᴏɴ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟʟᴏᴡ ᴛᴏ ɢᴇᴛ ᴅᴇsᴄʀɪᴘᴛɪᴏɴ ᴀʙᴏᴜᴛ sᴘᴇᴄɪғɪᴄs ᴄᴏᴍᴍᴀɴᴅ."""

EMI_IMG = "https://telegra.ph/file/ac69ea52fcc97749625f9.jpg"

DONATE_STRING = """ʜᴇʏᴀ, ɢʟᴀᴅ ᴛᴏ ʜᴇᴀʀ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴏɴᴀᴛᴇ!
 ʏᴏᴜ ᴄᴀɴ sᴜᴘᴘᴏʀᴛ ᴛʜᴇ ᴘʀᴏᴊᴇᴄᴛ ʙʏ ᴄᴏɴᴛᴀᴄᴛɪɴɢ sᴜᴍɪᴛ ʏᴀᴅᴀᴠ \
 sᴜᴘᴘᴏʀᴛɪɴɢ ɪsɴᴛ ᴀʟᴡᴀʏs ғɪɴᴀɴᴄɪᴀʟ! \
 ᴛʜᴏsᴇ ᴡʜᴏ ᴄᴀɴɴᴏᴛ ᴘʀᴏᴠɪᴅᴇ ᴍᴏɴᴇᴛᴀʀʏ sᴜᴘᴘᴏʀᴛ ᴀʀᴇ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ʜᴇʟᴘ ᴜs ᴅᴇᴠᴇʟᴏᴘ ᴛʜᴇ ʙᴏᴛ ᴀᴛ."""

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("EmikoRobot.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


def test(update: Update, context: CallbackContext):
    # pprint(eval(str(update)))
    # update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


def start(update: Update, context: CallbackContext):
    args = context.args
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="Go Back", callback_data="help_back")]]
                    ),
                )

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            first_name = update.effective_user.first_name
            update.effective_message.reply_text(
                PM_START_TEXT.format(
                    escape_markdown(first_name),
                    escape_markdown(uptime),
                    sql.num_users(),
                    sql.num_chats()),                        
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
            )
    else:
        update.effective_message.reply_text(
            f" ʜɪ, ɪ'ᴍ 🆉ᴇʙʀᴀ 🆁ᴏʙᴏᴛ. ɴɪᴄᴇ ᴛᴏ ᴍᴇᴇᴛ ʏᴏᴜ.",
            parse_mode=ParseMode.HTML
       )


def error_handler(update, context):
    """ʟᴏɢ ᴛʜᴇ ᴇʀʀᴏʀ ᴀɴᴅ sᴇɴᴅ ᴀ ᴛᴇʟᴇɢʀᴀᴍ ᴍᴇssᴀɢᴇ ᴛᴏ ɴᴏᴛɪғʏ ᴛʜᴇ ᴅᴇᴠᴇʟᴏᴘᴇʀ."""
    # ʟᴏɢ ᴛʜᴇ ᴇʀʀᴏʀ ʙᴇғᴏʀᴇ ᴡᴇ ᴅᴏ ᴀɴʏᴛʜɪɴɢ ᴇʟsᴇ, sᴏ ᴡᴇ ᴄᴀɴ sᴇᴇ ɪᴛ ᴇᴠᴇɴ ɪғ sᴏᴍᴇᴛʜɪɴɢ ʙʀᴇᴀᴋs.
    LOGGER.error(msg="ᴇxᴄᴇᴘᴛɪᴏɴ ᴡʜɪʟᴇ ʜᴀɴᴅʟɪɴɢ ᴀɴ ᴜᴘᴅᴀᴛᴇ:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # ʙᴜɪʟᴅ ᴛʜᴇ ᴍᴇssᴀɢᴇᴅ ᴡɪᴛʜ sᴏᴍᴇ ᴍᴀʀᴋᴜᴘ ᴀɴᴅ ᴀᴅᴅɪᴛɪᴏɴᴀʟ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ ᴡʜᴀᴛ ʜᴀᴘᴘᴇɴᴇᴅ.
    message = (
        "An exception was raised while handling an update\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    context.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML)


# for test purposes
def error_callback(update: Update, context: CallbackContext):
    error = context.error
    try:
        raise error
    except Unauthorized:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


def help_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    print(query.message.chat.id)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "Here is the help for the *{}* module:\n".format(
                    HELPABLE[module].__mod_name__
                )
                + HELPABLE[module].__help__
            )
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="Go Back", callback_data="help_back")]]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
        # query.message.delete()

    except BadRequest:
        pass


def emiko_about_callback(update, context):
    query = update.callback_query
    if query.data == "emiko_":
        query.message.edit_text(
            text="๏ ɪ'ᴍ *🆉ᴇʙʀᴀ 🆁ᴏʙᴏᴛ*, ᴀ ᴘᴏᴡᴇʀғᴜʟ ɢʀᴏᴜᴘ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ ʙᴏᴛ ʙᴜɪʟᴛ ᴛᴏ ʜᴇʟᴘ ʏᴏᴜ ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴇᴀsɪʟʏ."
            "\n• ɪ ᴄᴀɴ ʀᴇsᴛʀɪᴄᴛ ᴜsᴇʀs."
            "\n• ɪ ᴄᴀɴ ɢʀᴇᴇᴛ ᴜsᴇʀs ᴡɪᴛʜ ᴄᴜsᴛᴏᴍɪᴢᴀʙʟᴇ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇs ᴀɴᴅ ᴇᴠᴇɴ sᴇᴛ ᴀ ɢʀᴏᴜᴘ's ʀᴜʟᴇs."
            "\n• ɪ ʜᴀᴠᴇ ᴀɴ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀɴᴛɪ-ғʟᴏᴏᴅ sʏsᴛᴇᴍ."
            "\n• ɪ ᴄᴀɴ ᴡᴀʀɴ ᴜsᴇʀs ᴜɴᴛɪʟ ᴛʜᴇʏ ʀᴇᴀᴄʜ ᴍᴀx ᴡᴀʀɴs, ᴡɪᴛʜ ᴇᴀᴄʜ ᴘʀᴇᴅᴇғɪɴᴇᴅ ᴀᴄᴛɪᴏɴs sᴜᴄʜ ᴀs ʙᴀɴ, ᴍᴜᴛᴇ, ᴋɪᴄᴋ, ᴇᴛᴄ."
            "\n• ɪ ʜᴀᴠᴇ ᴀ ɴᴏᴛᴇ ᴋᴇᴇᴘɪɴɢ sʏsᴛᴇᴍ, ʙʟᴀᴄᴋʟɪsᴛs, ᴀɴᴅ ᴇᴠᴇɴ ᴘʀᴇᴅᴇᴛᴇʀᴍɪɴᴇᴅ ʀᴇᴘʟɪᴇs ᴏɴ ᴄᴇʀᴛᴀɪɴ ᴋᴇʏᴡᴏʀᴅs."
            "\n• ɪ ᴄʜᴇᴄᴋ ғᴏʀ ᴀᴅᴍɪɴs' ᴘᴇʀᴍɪssɪᴏɴs ʙᴇғᴏʀᴇ ᴇxᴇᴄᴜᴛɪɴɢ ᴀɴʏ ᴄᴏᴍᴍᴀɴᴅ ᴀɴᴅ ᴍᴏʀᴇ sᴛᴜғғs"
            "\n\n_🆉ᴇʙʀᴀ 🆁ᴏʙᴏᴛ's ʟɪᴄᴇɴsᴇᴅ ᴜɴᴅᴇʀ ᴛʜᴇ ɢɴᴜ ɢᴇɴᴇʀᴀʟ ᴘᴜʙʟɪᴄ ʟɪᴄᴇɴsᴇ ᴠ3.0_"
            "\n\n ᴄʟɪᴄᴋ ᴏɴ ʙᴜᴛᴛᴏɴ ʙᴇʟʟᴏᴡ ᴛᴏ ɢᴇᴛ ʙᴀsɪᴄ ʜᴇʟᴘ ғᴏʀ 🆉ᴇʙʀᴀ 🆁ᴏʙᴏᴛ.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="ᴀᴅᴍɪɴs", callback_data="emiko_admin"),
                    InlineKeyboardButton(text="ɴᴏᴛᴇs", callback_data="emiko_notes"),
                 ],
                 [
                    InlineKeyboardButton(text="sᴜᴘᴘᴏʀᴛ", callback_data="emiko_support"),
                    InlineKeyboardButton(text="ᴄʀᴇᴅɪᴛs", callback_data="emiko_credit"),
                 ],
                 [
                    InlineKeyboardButton(text="ʏᴏᴜᴛᴜʙᴇ", url="https://youtube.com/channel/UCtI7hbY-BD7wvuIzoSU0cEw"),
                 ],
                 [
                    InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="emiko_back"),
                 ]
                ]
            ),
        )
    elif query.data == "emiko_back":
        first_name = update.effective_user.first_name
        uptime = get_readable_time((time.time() - StartTime))
        query.message.edit_text(
                PM_START_TEXT.format(
                    escape_markdown(first_name),
                    escape_markdown(uptime),
                    sql.num_users(),
                    sql.num_chats()),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )

    elif query.data == "emiko_admin":
        query.message.edit_text(
            text=f"*๏ ʟᴇᴛ's ᴍᴀᴋᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ ʙɪᴛ ᴇғғᴇᴄᴛɪᴠᴇ ɴᴏᴡ*"
            "\nᴄᴏɴɢʀᴀɢᴜʟᴀᴛɪᴏɴ ʙᴏᴛ ɴᴏᴡ ʀᴇᴀᴅʏ ᴛᴏ ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ."
            "\n\n*ᴀᴅᴍɪɴ ᴛᴏᴏʟs*"
            "\nʙᴀsɪᴄ ᴀᴅᴍɪɴ ᴛᴏᴏʟs ʜᴇʟᴘ ʏᴏᴜ ᴛᴏ ᴘʀᴏᴛᴇᴄᴛ ᴀɴᴅ ᴘᴏᴡᴇʀᴜᴘ ʏᴏᴜʀ ɢʀᴏᴜᴘ."
            "\nʏᴏᴜ ᴄᴀɴ ʙᴀɴ ᴍᴇᴍʙᴇʀs, ᴋɪᴄᴋ ᴍᴇᴍʙᴇʀs, ᴘʀᴏᴍᴏᴛᴇ sᴏᴍᴇᴏɴᴇ ᴀs ᴀᴅᴍɪɴ ᴛʜʀᴏᴜɢʜ ᴄᴏᴍᴍᴀɴᴅs ᴏғ ʙᴏᴛ."
            "\n\n*ɢʀᴇᴇᴛɪɴɢs*"
            "\nʟᴇᴛs sᴇᴛ ᴀ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ ᴛᴏ ᴡᴇʟᴄᴏᴍᴇ ɴᴇᴡ ᴜsᴇʀs ᴄᴏᴍɪɴɢ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ."
            "\nsᴇɴᴅ `/setwelcome [message]` ᴛᴏ sᴇᴛ ᴀ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ!",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Go Back", callback_data="emiko_")]]
            ),
        )

    elif query.data == "emiko_notes":
        query.message.edit_text(
            text=f"<b>๏ sᴇᴛᴛɪɴɢ ᴜᴘ ɴᴏᴛᴇs</b>"
            f"\nʏᴏᴜ ᴄᴀɴ sᴀᴠᴇ ᴍᴇssᴀɢᴇ/ᴍᴇᴅɪᴀ/ᴀᴜᴅɪᴏ ᴏʀ ᴀɴʏᴛʜɪɴɢ ᴀs ɴᴏᴛᴇs"
            f"\nto ɢᴇᴛ ᴀ ɴᴏᴛᴇ sɪᴍᴘʟʏ ᴜsᴇ # ᴀᴛ ᴛʜᴇ ʙᴇɢɪɴɴɪɴɢ ᴏғ ᴀ ᴡᴏʀᴅ"
            f"\n\ɴʏᴏᴜ ᴄᴀɴ ᴀʟsᴏ sᴇᴛ ʙᴜᴛᴛᴏɴs ғᴏʀ ɴᴏᴛᴇs ᴀɴᴅ ғɪʟᴛᴇʀs (ʀᴇғᴇʀ ʜᴇʟᴘ ᴍᴇɴᴜ)",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Go Back", callback_data="emiko_")]]
            ),
        )
    elif query.data == "emiko_support":
        query.message.edit_text(
            text="*๏ 🆉ᴇʙʀᴀ 🆁ᴏʙᴏᴛ sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛs*"
            "\nᴊᴏɪɴ ᴍʏ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ғᴏʀ sᴇᴇ ᴏʀ ʀᴇᴘᴏʀᴛ ᴀ ᴘʀᴏʙʟᴇᴍ ᴏɴ 🆉ᴇʙʀᴀ 🆁ᴏʙᴏᴛ.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="sᴜᴘᴘᴏʀᴛ", url="t.me/World_FriendShip_Zone"),
                    InlineKeyboardButton(text="ᴜᴘᴅᴀᴛᴇs", url="https://t.me/The_Superior_Network"),
                 ],
                 [
                    InlineKeyboardButton(text="ɢᴏ ʙᴀᴄᴋ", callback_data="emiko_"),
                 
                 ]
                ]
            ),
        )


    elif query.data == "emiko_credit":
        query.message.edit_text(
            text=f"๏ ᴄʀᴇᴅɪs ғᴏʀ 🆉ᴇʙʀᴀ 🆁ᴏʙᴏᴛ\n"
            "\nʜᴇʀᴇ ᴅᴇᴠᴇʟᴏᴘᴇʀs ᴍᴀᴋɪɴɢ ᴀɴᴅ ɢɪᴠᴇ ɪɴsᴘɪʀᴀᴛɪᴏɴ ғᴏʀ ᴍᴀᴅᴇ ᴛʜᴇ 🆉ᴇʙʀᴀ 🆁ᴏʙᴏᴛ",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="sᴜᴍɪᴛ ʏᴀᴅᴀᴠ", url="https://t.me/Simple_Mundaa"),
                    InlineKeyboardButton(text="ɴɪᴋɪᴛᴀ", url="https://t.me/Cute_Shezhadi012"),
                 ],
                 
                ]
            ),
        )

def Source_about_callback(update, context):
    query = update.callback_query
    if query.data == "source_":
        query.message.edit_text(
            text="๏›› ᴛʜɪs ᴀᴅᴠᴀɴᴄᴇ ᴄᴏᴍᴍᴀɴᴅ ғᴏʀ ᴍᴜsɪᴄᴘʟᴀʏᴇʀ."
            "\n\n๏ ᴄᴏᴍᴍᴀɴᴅ ғᴏʀ ᴀᴅᴍɪɴs ᴏɴʟʏ."
            "\n • `/reload` - ғᴏʀ ʀᴇғʀᴇsʜɪɴɢ ᴛʜᴇ ᴀᴅᴍɪɴʟɪsᴛ."
            "\n • `/pause` - ᴛᴏ ᴘᴀᴜsᴇ ᴛʜᴇ ᴘʟᴀʏʙᴀᴄᴋ."
            "\n • `/resume` - ᴛᴏ ʀᴇsᴜᴍɪɴɢ ᴛʜᴇ ᴘʟᴀʏʙᴀᴄᴋ ʏᴏᴜ'ᴠᴇ ᴘᴀᴜsᴇᴅ."
            "\n • `/skip` - ᴛᴏ sᴋɪᴘᴘɪɴɢ ᴛʜᴇ ᴘʟᴀʏᴇʀ."
            "\n • `/end` - ғᴏʀ ᴇɴᴅ ᴛʜᴇ ᴘʟᴀʏʙᴀᴄᴋ."
            "\n • `/ᴍᴜsɪᴄᴘʟᴀʏᴇʀ <on/off>` - ᴛᴏɢɢʟᴇ ғᴏʀ ᴛᴜʀɴ ᴏɴ ᴏʀ ᴛᴜʀɴ ᴏғғ ᴛʜᴇ ᴍᴜsɪᴄᴘʟᴀʏᴇʀ."
            "\n\n๏ ᴄᴏᴍᴍᴀɴᴅ ғᴏʀ ᴀʟʟ ᴍᴇᴍʙᴇʀs."
            "\n • `/play` <ǫᴜᴇʀʏ /ʀᴇᴘʟʏ ᴀᴜᴅɪᴏ> - ᴘʟᴀʏɪɴɢ ᴍᴜsɪᴄ ᴠɪᴀ ʏᴏᴜᴛᴜʙᴇ."
            "\n • `/playlist` - ᴛᴏ ᴘʟᴀʏɪɴɢ ᴀ ᴘʟᴀʏʟɪsᴛ ᴏғ ɢʀᴏᴜᴘs ᴏʀ ʏᴏᴜʀ ᴘᴇʀsᴏɴᴀʟ ᴘʟᴀʏʟɪsᴛ",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Go Back", callback_data="emiko_")
                 ]
                ]
            ),
        )
    elif query.data == "source_back":
        first_name = update.effective_user.first_name
        query.message.edit_text(
                PM_START_TEXT.format(
                    escape_markdown(first_name),
                    escape_markdown(uptime),
                    sql.num_users(),
                    sql.num_chats()),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )

def get_help(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:
        if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
            module = args[1].lower()
            update.effective_message.reply_text(
                f"Contact me in PM to get help of {module.capitalize()}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Help",
                                url="t.me/{}?start=ghelp_{}".format(
                                    context.bot.username, module
                                ),
                            )
                        ]
                    ]
                ),
            )
            return
        update.effective_message.reply_text(
            "Contact me in PM to get the list of possible commands.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Help",
                            url="t.me/{}?start=help".format(context.bot.username),
                        )
                    ]
                ]
            ),
        )
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "Here is the available help for the *{}* module:\n".format(
                HELPABLE[module].__mod_name__
            )
            + HELPABLE[module].__help__
        )
        send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Go Back", callback_data="help_back")]]
            ),
        )

    else:
        send_help(chat.id, HELP_STRINGS)


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            dispatcher.bot.send_message(
                user_id,
                "sᴇᴇᴍs ʟɪᴋᴇ ᴛʜᴇʀᴇ ᴀʀᴇɴ'ᴛ ᴀɴʏ ᴜsᴇʀ sᴘᴇᴄɪғɪᴄ sᴇᴛᴛɪɴɢs ᴀᴠᴀɪʟᴀʙʟᴇ :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(
                user_id,
                text="Which module would you like to check {}'s settings for?".format(
                    chat_name
                ),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )
        else:
            dispatcher.bot.send_message(
                user_id,
                "sᴇᴇᴍs ʟɪᴋᴇ ᴛʜᴇʀᴇ ᴀʀᴇɴ'ᴛ ᴀɴʏ ᴄʜᴀᴛ sᴇᴛᴛɪɴɢs ᴀᴠᴀɪʟᴀʙʟᴇ :'(\nsᴇɴᴅ ᴛʜɪs "
                "ɪɴ ᴀ ɢʀᴏᴜᴘ ᴄʜᴀᴛ ʏᴏᴜ'ʀᴇ ᴀᴅᴍɪɴ ɪɴ ᴛᴏ ғɪɴᴅ ɪᴛs ᴄᴜʀʀᴇɴᴛ sᴇᴛᴛɪɴɢs!",
                parse_mode=ParseMode.MARKDOWN,
            )


def settings_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user
    bot = context.bot
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.reply_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Go Back",
                                callback_data="stngs_back({})".format(chat_id),
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                text="Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
        query.message.delete()
    except BadRequest as excp:
        if excp.message not in [
            "Message is not modified",
            "Query_id_invalid",
            "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))


def get_settings(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "Click here to get this chat's settings, as well as yours."
            msg.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Settings",
                                url="t.me/{}?start=stngs_{}".format(
                                    context.bot.username, chat.id
                                ),
                            )
                        ]
                    ]
                ),
            )
        else:
            text = "Click here to check your settings."

    else:
        send_settings(chat.id, user.id, True)


def donate(update: Update, context: CallbackContext):
    user = update.effective_message.from_user
    chat = update.effective_chat  # type: Optional[Chat]
    bot = context.bot
    if chat.type == "private":
        update.effective_message.reply_text(
            DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )

        if OWNER_ID != 5009839424:
            update.effective_message.reply_text(
                "ɪ'ᴍ ғʀᴇᴇ ғᴏʀ ᴇᴠᴇʀʏᴏɴᴇ ❤️ ɪғ ʏᴏᴜ ᴡᴀɴɴᴀ ᴍᴀᴋᴇ ᴍᴇ sᴍɪʟᴇ, ᴊᴜsᴛ ᴊᴏɪɴ"
                "[My Channel]({})".format(DONATION_LINK),
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        try:
            bot.send_message(
                user.id,
                DONATE_STRING,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )

            update.effective_message.reply_text(
                "ɪ'ᴠᴇ ᴘᴍ'ᴇᴅ ʏᴏᴜ ᴀʙᴏᴜᴛ ᴅᴏɴᴀᴛɪɴɢ ᴛᴏ ᴍʏ ᴄʀᴇᴀᴛᴏʀ sᴜᴍɪᴛ ʏᴀᴅᴀᴠ!"
            )
        except Unauthorized:
            update.effective_message.reply_text(
                "ᴄᴏɴᴛᴀᴄᴛ ᴍᴇ ɪɴ ᴘᴍ ғɪʀsᴛ ᴛᴏ ɢᴇᴛ ᴅᴏɴᴀᴛɪᴏɴ ɪɴғᴏʀᴍᴀᴛɪᴏɴ."
            )


def migrate_chats(update: Update, context: CallbackContext):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop


def main():

    if SUPPORT_CHAT is not None and isinstance(SUPPORT_CHAT, str):
        try:
            dispatcher.bot.sendMessage(
                f"@{SUPPORT_CHAT}", 
                " ʜɪ, ɪ'ᴍ ᴀʟɪᴠᴇ😂.",
                parse_mode=ParseMode.MARKDOWN
            )
        except Unauthorized:
            LOGGER.warning(
                "ʙᴏᴛ ɪsɴᴛ ᴀʙʟᴇ ᴛᴏ sᴇɴᴅ ᴍᴇssᴀɢᴇ ᴛᴏ sᴜᴘᴘᴏʀᴛ_ᴄʜᴀᴛ, ɢᴏ ᴀɴᴅ ᴄʜᴇᴄᴋ!"
            )
        except BadRequest as e:
            LOGGER.warning(e.message)

    test_handler = CommandHandler("test", test, run_async=True)
    start_handler = CommandHandler("start", start, run_async=True)

    help_handler = CommandHandler("help", get_help, run_async=True)
    help_callback_handler = CallbackQueryHandler(
        help_button, pattern=r"help_.*", run_async=True
    )

    settings_handler = CommandHandler("settings", get_settings, run_async=True)
    settings_callback_handler = CallbackQueryHandler(
        settings_button, pattern=r"stngs_", run_async=True
    )

    about_callback_handler = CallbackQueryHandler(
        emiko_about_callback, pattern=r"emiko_", run_async=True
    )

    source_callback_handler = CallbackQueryHandler(
        Source_about_callback, pattern=r"source_", run_async=True
    )

    donate_handler = CommandHandler("donate", donate, run_async=True)
    migrate_handler = MessageHandler(
        Filters.status_update.migrate, migrate_chats, run_async=True
    )

    dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(about_callback_handler)
    dispatcher.add_handler(source_callback_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    dispatcher.add_handler(donate_handler)

    dispatcher.add_error_handler(error_callback)

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN, certificate=open(CERT_PATH, "rb"))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)

    else:
        LOGGER.info("Using long polling.")
        updater.start_polling(timeout=15, read_latency=4, drop_pending_updates=True)

    if len(argv) not in (1, 3, 4):
        telethn.disconnect()
    else:
        telethn.run_until_disconnected()

    updater.idle()


if __name__ == "__main__":
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    telethn.start(bot_token=TOKEN)
    pbot.start()
    main()
