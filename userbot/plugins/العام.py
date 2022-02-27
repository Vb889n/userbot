import asyncio
from datetime import datetime

from telethon.errors import BadRequestError
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import ChatBannedRights
from telethon.utils import get_display_name

from userbot import jmthon

from ..core.managers import edit_delete, edit_or_reply
from ..helpers.utils import _format
from ..sql_helper import gban_sql_helper as gban_sql
from ..sql_helper.mute_sql import is_muted, mute, unmute
from . import BOTLOG, BOTLOG_CHATID, admin_groups, get_user_from_event

plugin_category = "admin"

BANNED_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)

UNBAN_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=None,
    send_media=None,
    send_stickers=None,
    send_gifs=None,
    send_games=None,
    send_inline=None,
    embed_links=None,
)


@jmthon.ar_cmd(
    pattern="حظر_عام(?:\s|$)([\s\S]*)",
    command=("حظر_عام", plugin_category),
    info={
        "header": "لحظر المستخدم في جميع المجموعات التي تكون بها مشرف.",
        "description": "لحظر المستخدم في جميع المجموعات.",
        "usage": "{tr}حظر_عام <معرف/بالرد/ايدي> <السبب (اختياري)>",
    },
)
async def jmthongban(event):  # sourcery no-metrics
    "لحظر المستخدم في جميع المجموعات التي تكون بها مشرف."
    jmthone = await edit_or_reply(event, "**- جارِ حظر هذا المستخدم انتظر**")
    start = datetime.now()
    user, reason = await get_user_from_event(event, jmthone)
    if not user:
        return
    if user.id == jmthon.uid:
        return await edit_delete(jmthone, "- عذرا لا يمكنني حظر نفسي ")
    if gban_sql.is_gbanned(user.id):
        await jmthone.edit(
            f"[المستخدم](tg://user?id={user.id})**هو بالفعل في قائمه الحظر العام**"
        )
    else:
        gban_sql.jmthongban(user.id, reason)
    san = await admin_groups(event.client)
    count = 0
    sandy = len(san)
    if sandy == 0:
        return await edit_delete(jmthone, "-**يجب ان تكون في مجموعه واحده على الاقل**")
    await jmthone.edit(
        f"**يتم بدء حظر** [المستخدم](tg://user?id={user.id}) **في  {len(san)} من المجموعات**"
    )
    for i in range(sandy):
        try:
            await event.client(EditBannedRequest(san[i], user.id, BANNED_RIGHTS))
            await asyncio.sleep(0.5)
            count += 1
        except BadRequestError:
            achat = await event.client.get_entity(san[i])
            await event.client.send_message(
                BOTLOG_CHATID,
                f"- ليست لديك صلاحيات في  :\n**الدردشه :** {get_display_name(achat)}(`{achat.id}`)\nلحظر المستخدمين فيها",
            )
    end = datetime.now()
    jmthontaken = (end - start).seconds
    if reason:
        await jmthone.edit(
            f"[{user.first_name}](tg://user?id={user.id}) تم حظره في {count} من المجموعات في {jmthontaken} ثواني \n**السبب :** `{reason}`"
        )
    else:
        await jmthone.edit(
            f"[{user.first_name}](tg://user?id={user.id}) تم حظره في {count} من المجموعات في {jmthontaken} ثواني"
        )
    if BOTLOG and count != 0:
        reply = await event.get_reply_message()
        if reason:
            await event.client.send_message(
                BOTLOG_CHATID,
                f"#حظر_عام\
                \nالحظر العام\
                \n**المستخدم : **[{user.first_name}](tg://user?id={user.id})\
                \n**الايدي : **`{user.id}`\
                \n**السبب :** `{reason}`\
                \n__تم حظره في {count} من المجموعات__\
                \n**الوقت المستغرق : **`{jmthontaken} ثواني`",
            )
        else:
            await event.client.send_message(
                BOTLOG_CHATID,
                f"#حظر_عام\
                \nالحظر العام\
                \n**المستخدم : **[{user.first_name}](tg://user?id={user.id})\
                \n**الايدي : **`{user.id}`\
                \n__تم حظره في {count} من المجموعات__\
                \n**الوقت المستغرق : **`{jmthontaken} ثواني`",
            )
        try:
            if reply:
                await reply.forward_to(BOTLOG_CHATID)
                await reply.delete()
        except BadRequestError:
            pass


@jmthon.ar_cmd(
    pattern="الغاء_حظر(?:\s|$)([\s\S]*)",
    command=("الغاء_حظر", plugin_category),
    info={
        "header": "To unban the person from every group where you are admin.",
        "description": "will unban and also remove from your gbanned list.",
        "usage": "{tr}الغاء_حظر <معرف/بالرد/ايدي>",
    },
)
async def jmthongban(event):
    "To unban the person from every group where you are admin."
    jmthone = await edit_or_reply(event, "`ungbanning.....`")
    start = datetime.now()
    user, reason = await get_user_from_event(event, jmthone)
    if not user:
        return
    if gban_sql.is_gbanned(user.id):
        gban_sql.jmthonungban(user.id)
    else:
        return await edit_delete(
            jmthone, f"the [user](tg://user?id={user.id}) `is not in your gbanned list`"
        )
    san = await admin_groups(event.client)
    count = 0
    sandy = len(san)
    if sandy == 0:
        return await edit_delete(jmthone, "`you are not even admin of atleast one group `")
    await jmthone.edit(
        f"initiating ungban of the [user](tg://user?id={user.id}) in `{len(san)}` groups"
    )
    for i in range(sandy):
        try:
            await event.client(EditBannedRequest(san[i], user.id, UNBAN_RIGHTS))
            await asyncio.sleep(0.5)
            count += 1
        except BadRequestError:
            achat = await event.client.get_entity(san[i])
            await event.client.send_message(
                BOTLOG_CHATID,
                f"`You don't have required permission in :`\n**Chat :** {get_display_name(achat)}(`{achat.id}`)\n`For Unbanning here`",
            )
    end = datetime.now()
    jmthontaken = (end - start).seconds
    if reason:
        await jmthone.edit(
            f"[{user.first_name}](tg://user?id={user.id}`) was ungbanned in {count} groups in {jmthontaken} seconds`!!\n**Reason :** `{reason}`"
        )
    else:
        await jmthone.edit(
            f"[{user.first_name}](tg://user?id={user.id}) `was ungbanned in {count} groups in {jmthontaken} seconds`!!"
        )

    if BOTLOG and count != 0:
        if reason:
            await event.client.send_message(
                BOTLOG_CHATID,
                f"#UNGBAN\
                \nGlobal Unban\
                \n**User : **[{user.first_name}](tg://user?id={user.id})\
                \n**ID : **`{user.id}`\
                \n**Reason :** `{reason}`\
                \n__Unbanned in {count} groups__\
                \n**Time taken : **`{jmthontaken} seconds`",
            )
        else:
            await event.client.send_message(
                BOTLOG_CHATID,
                f"#UNGBAN\
                \nGlobal Unban\
                \n**User : **[{user.first_name}](tg://user?id={user.id})\
                \n**ID : **`{user.id}`\
                \n__Unbanned in {count} groups__\
                \n**Time taken : **`{jmthontaken} seconds`",
            )


@jmthon.ar_cmd(
    pattern="listgban$",
    command=("listgban", plugin_category),
    info={
        "header": "Shows you the list of all gbanned users by you.",
        "usage": "{tr}listgban",
    },
)
async def gablist(event):
    "Shows you the list of all gbanned users by you."
    gbanned_users = gban_sql.get_all_gbanned()
    GBANNED_LIST = "Current Gbanned Users\n"
    if len(gbanned_users) > 0:
        for a_user in gbanned_users:
            if a_user.reason:
                GBANNED_LIST += f"👉 [{a_user.chat_id}](tg://user?id={a_user.chat_id}) for {a_user.reason}\n"
            else:
                GBANNED_LIST += (
                    f"👉 [{a_user.chat_id}](tg://user?id={a_user.chat_id}) Reason None\n"
                )
    else:
        GBANNED_LIST = "no Gbanned Users (yet)"
    await edit_or_reply(event, GBANNED_LIST)


@jmthon.ar_cmd(
    pattern="gmute(?:\s|$)([\s\S]*)",
    command=("gmute", plugin_category),
    info={
        "header": "To mute a person in all groups where you are admin.",
        "description": "It doesnt change user permissions but will delete all messages sent by him in the groups where you are admin including in private messages.",
        "usage": "{tr}gmute username/reply> <reason (optional)>",
    },
)
async def startgmute(event):
    "To mute a person in all groups where you are admin."
    if event.is_private:
        await event.edit("`Unexpected issues or ugly errors may occur!`")
        await asyncio.sleep(2)
        userid = event.chat_id
        reason = event.pattern_match.group(1)
    else:
        user, reason = await get_user_from_event(event)
        if not user:
            return
        if user.id == jmthon.uid:
            return await edit_or_reply(event, "`Sorry, I can't gmute myself`")
        userid = user.id
    try:
        user = (await event.client(GetFullUserRequest(userid))).user
    except Exception:
        return await edit_or_reply(event, "`Sorry. I am unable to fetch the user`")
    if is_muted(userid, "gmute"):
        return await edit_or_reply(
            event,
            f"{_format.mentionuser(user.first_name ,user.id)} ` is already gmuted`",
        )
    try:
        mute(userid, "gmute")
    except Exception as e:
        await edit_or_reply(event, f"**Error**\n`{e}`")
    else:
        if reason:
            await edit_or_reply(
                event,
                f"{_format.mentionuser(user.first_name ,user.id)} `is Successfully gmuted`\n**Reason :** `{reason}`",
            )
        else:
            await edit_or_reply(
                event,
                f"{_format.mentionuser(user.first_name ,user.id)} `is Successfully gmuted`",
            )
    if BOTLOG:
        reply = await event.get_reply_message()
        if reason:
            await event.client.send_message(
                BOTLOG_CHATID,
                "#GMUTE\n"
                f"**User :** {_format.mentionuser(user.first_name ,user.id)} \n"
                f"**Reason :** `{reason}`",
            )
        else:
            await event.client.send_message(
                BOTLOG_CHATID,
                "#GMUTE\n"
                f"**User :** {_format.mentionuser(user.first_name ,user.id)} \n",
            )
        if reply:
            await reply.forward_to(BOTLOG_CHATID)


@jmthon.ar_cmd(
    pattern="ungmute(?:\s|$)([\s\S]*)",
    command=("ungmute", plugin_category),
    info={
        "header": "To unmute the person in all groups where you were admin.",
        "description": "This will work only if you mute that person by your gmute command.",
        "usage": "{tr}ungmute <username/reply>",
    },
)
async def endgmute(event):
    "To remove gmute on that person."
    if event.is_private:
        await event.edit("`Unexpected issues or ugly errors may occur!`")
        await asyncio.sleep(2)
        userid = event.chat_id
        reason = event.pattern_match.group(1)
    else:
        user, reason = await get_user_from_event(event)
        if not user:
            return
        if user.id == jmthon.uid:
            return await edit_or_reply(event, "`Sorry, I can't gmute myself`")
        userid = user.id
    try:
        user = (await event.client(GetFullUserRequest(userid))).user
    except Exception:
        return await edit_or_reply(event, "`Sorry. I am unable to fetch the user`")
    if not is_muted(userid, "gmute"):
        return await edit_or_reply(
            event, f"{_format.mentionuser(user.first_name ,user.id)} `is not gmuted`"
        )
    try:
        unmute(userid, "gmute")
    except Exception as e:
        await edit_or_reply(event, f"**Error**\n`{e}`")
    else:
        if reason:
            await edit_or_reply(
                event,
                f"{_format.mentionuser(user.first_name ,user.id)} `is Successfully ungmuted`\n**Reason :** `{reason}`",
            )
        else:
            await edit_or_reply(
                event,
                f"{_format.mentionuser(user.first_name ,user.id)} `is Successfully ungmuted`",
            )
    if BOTLOG:
        if reason:
            await event.client.send_message(
                BOTLOG_CHATID,
                "#UNGMUTE\n"
                f"**User :** {_format.mentionuser(user.first_name ,user.id)} \n"
                f"**Reason :** `{reason}`",
            )
        else:
            await event.client.send_message(
                BOTLOG_CHATID,
                "#UNGMUTE\n"
                f"**User :** {_format.mentionuser(user.first_name ,user.id)} \n",
            )


@jmthon.ar_cmd(incoming=True)
async def watcher(event):
    if is_muted(event.sender_id, "gmute"):
        await event.delete()


@jmthon.ar_cmd(
    pattern="gkick(?:\s|$)([\s\S]*)",
    command=("gkick", plugin_category),
    info={
        "header": "kicks the person in all groups where you are admin.",
        "usage": "{tr}gkick <username/reply/userid> <reason (optional)>",
    },
)
async def jmthongkick(event):  # sourcery no-metrics
    "kicks the person in all groups where you are admin"
    jmthone = await edit_or_reply(event, "`gkicking.......`")
    start = datetime.now()
    user, reason = await get_user_from_event(event, jmthone)
    if not user:
        return
    if user.id == jmthon.uid:
        return await edit_delete(jmthone, "`why would I kick myself`")
    san = await admin_groups(event.client)
    count = 0
    sandy = len(san)
    if sandy == 0:
        return await edit_delete(jmthone, "`you are not admin of atleast one group` ")
    await jmthone.edit(
        f"`initiating gkick of the `[user](tg://user?id={user.id}) `in {len(san)} groups`"
    )
    for i in range(sandy):
        try:
            await event.client.kick_participant(san[i], user.id)
            await asyncio.sleep(0.5)
            count += 1
        except BadRequestError:
            achat = await event.client.get_entity(san[i])
            await event.client.send_message(
                BOTLOG_CHATID,
                f"`You don't have required permission in :`\n**Chat :** {get_display_name(achat)}(`{achat.id}`)\n`For kicking there`",
            )
    end = datetime.now()
    jmthontaken = (end - start).seconds
    if reason:
        await jmthone.edit(
            f"[{user.first_name}](tg://user?id={user.id}) `was gkicked in {count} groups in {jmthontaken} seconds`!!\n**Reason :** `{reason}`"
        )
    else:
        await jmthone.edit(
            f"[{user.first_name}](tg://user?id={user.id}) `was gkicked in {count} groups in {jmthontaken} seconds`!!"
        )

    if BOTLOG and count != 0:
        reply = await event.get_reply_message()
        if reason:
            await event.client.send_message(
                BOTLOG_CHATID,
                f"#GKICK\
                \nGlobal Kick\
                \n**User : **[{user.first_name}](tg://user?id={user.id})\
                \n**ID : **`{user.id}`\
                \n**Reason :** `{reason}`\
                \n__Kicked in {count} groups__\
                \n**Time taken : **`{jmthontaken} seconds`",
            )
        else:
            await event.client.send_message(
                BOTLOG_CHATID,
                f"#GKICK\
                \nGlobal Kick\
                \n**User : **[{user.first_name}](tg://user?id={user.id})\
                \n**ID : **`{user.id}`\
                \n__Kicked in {count} groups__\
                \n**Time taken : **`{jmthontaken} seconds`",
            )
        if reply:
            await reply.forward_to(BOTLOG_CHATID)
