import asyncio, json, os, random, re, time
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights

# --- [ الاعدادات الاساسية - كيرتا V2.3 المطور ] ---
API_ID = 38559489 
API_HASH = "0f8ecc31ec7aebebe82e7bb17fc785e3"
OWNER_ID = 8431180189

if not os.path.exists("sessions"): os.makedirs("sessions")
if not os.path.exists("words"): os.makedirs("words")
if not os.path.exists("deleted_pm"): os.makedirs("deleted_pm")

all_tasks, all_hunter_tasks, all_muted_users, login_data = {}, {}, {}, {}
barad_settings = {}
auto_bot_reply = {}  
bot_running = {}  
add_mode = {}  
original_profile = {}  

pm_cache = {}      
spy_words = {}     
active_sessions = {}

def is_auth(sid):
    if sid == OWNER_ID:
        return True
    if os.path.exists("subs.json"):
        try:
            with open("subs.json", "r", encoding="utf-8") as f:
                subs = json.load(f)
            return sid in subs
        except Exception:
            return False
    return False

def get_user_words(uid, cmd):
    path = f"words/{uid}_{cmd}.txt"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    if cmd == "ym":
        return ["رد عشوائي", "هلا", "نعم"]
    elif cmd == "drb":
        return ["كس امك", "يا منيوك"]
    elif cmd == "khlt":
        return ["مفروش", "طحين"]
    elif cmd == "blash":
        return ["ابن قحبه", "كل زق"]
    return ["رد عشوائي"]

def parse_barad_text(text):
    clean_text = text.replace("،", " ").replace(",", " ")
    words = clean_text.split()
    if not words: return None
    
    result = []
    is_valid_barad = False
    
    for word in words:
        match = re.match(r"^([^\(]+)\((\d+)\)$", word)
        if match:
            is_valid_barad = True
            w = match.group(1).strip()
            count = int(match.group(2))
            result.extend([w] * count)
        else:
            if len(word) < 15:
                result.append(word)
            else:
                return None

    if is_valid_barad or (" layout" not in text and ("،" in text or "," in text) and len(words) >= 2):
        return " ".join(result)
        
    return None

# --- [ محرك كيرتا V2.3 ] ---
def register_handlers(bot, bot_id):
    uid = bot_id
    all_tasks[uid], all_hunter_tasks[uid], all_muted_users[uid] = {}, {}, []
    
    pm_cache[uid] = {}
    spy_words[uid] = []
    active_sessions[uid] = bot
    
    if uid not in barad_settings:
        barad_settings[uid] = {"active_chats": [], "speed": 0.1}

    @bot.on(events.NewMessage(incoming=True))
    async def save_pm(event):
        if not bot_running.get(uid, True): return
        if not event.is_private or event.out: return
        
        sender = await event.get_sender()
        sender_name = sender.first_name if sender else "غير معروف"
        
        file_path = None
        if event.media:
            try:
                is_view_once = False
                if hasattr(event.media, 'ttl_seconds') and event.media.ttl_seconds:
                    is_view_once = True
                
                file_path = await event.download_media(file="deleted_pm/")
                
                if is_view_once and file_path:
                    caption = (
                        "--- RADAR DETECTION : VIEW ONCE MEDIA ---\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"SENDER : {sender_name}\n"
                        f"NOTE : الصوره المحذوفه\n"
                        "━━━━━━━━━━━━━━━━━━━━━━"
                    )
                    await bot.send_file("me", file_path, caption=caption, parse_mode='html')
                    if os.path.exists(file_path): os.remove(file_path)
                    return 
            except: pass

        if uid in pm_cache:
            pm_cache[uid][event.id] = {
                "text": event.text or "",
                "sender": sender_name,
                "file": file_path
            }

    @bot.on(events.MessageDeleted())
    async def deleted_pm_handler(event):
        if uid not in pm_cache: return
        for msg_id in event.deleted_ids:
            if msg_id in pm_cache[uid]:
                data = pm_cache[uid][msg_id]
                sender = data['sender']
                text = data['text']
                
                if data["file"]:
                    caption = (
                        "--- RADAR DETECTION : MEDIA ---\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"SENDER : {sender}\n"
                        f"CAPTION : ||{text or 'لا يوجد'}||\n"
                        "━━━━━━━━━━━━━━━━━━━━━━"
                    )
                    try:
                        await bot.send_file("me", data["file"], caption=caption, parse_mode='html')
                        if os.path.exists(data["file"]): os.remove(data["file"])
                    except: pass
                else:
                    caption = (
                        "--- RADAR DETECTION : TEXT ---\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"SENDER : {sender}\n"
                        f"MESSAGE : ||{text}||\n"
                        "━━━━━━━━━━━━━━━━━━━━━━"
                    )
                    try: 
                        await bot.send_message("me", caption, parse_mode='html')
                    except: pass
                    
                del pm_cache[uid][msg_id]

    @bot.on(events.NewMessage(incoming=True))
    async def spy_radar(event):
        if not bot_running.get(uid, True): return
        if not event.text or not spy_words.get(uid): return
        for word in spy_words[uid]:
            if word in event.text:
                chat = await event.get_chat()
                chat_title = getattr(chat, 'title', 'خاص')
                sender = await event.get_sender()
                sender_name = sender.first_name if sender else "غير معروف"
                report = (
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"CHAT   : {chat_title}\n"
                    f"SENDER : {sender_name}\n"
                    f"WORD   : {word}\n"
                    f"TEXT   : {event.text}\n"
                    "━━━━━━━━━━━━━━━━━━━━━━"
                )
                try:
                    await bot.send_message("me", report)
                except: pass
                break

    @bot.on(events.NewMessage(incoming=True))
    async def barad_engine(e):
        if not bot_running.get(uid, True): return
        active_chats = barad_settings.get(uid, {}).get("active_chats", [])
        if e.chat_id not in active_chats: return
        if not e.text or e.out: return
        
        processed_text = parse_barad_text(e.text)
        if processed_text and processed_text.strip() != e.text.strip():
            await asyncio.sleep(barad_settings[uid]["speed"])
            await e.respond(processed_text)

    if uid not in auto_bot_reply:
        auto_bot_reply[uid] = set()
    if uid not in bot_running:
        bot_running[uid] = True

    @bot.on(events.NewMessage(incoming=True))
    async def auto_reply_to_bots(event):
        if not bot_running.get(uid, True):
            return
        if event.chat_id not in auto_bot_reply.get(uid, set()):
            return
        if not event.text or event.out:
            return
        try:
            sender = await event.get_sender()
            if not sender or not getattr(sender, "bot", False):
                return
            match = re.fullmatch(
                r"\s*•\s*اكتب\s*(?:↤|←|⬅|⇦)\s*\(\s*([^()\n]+?)\s*\)\s*",
                event.raw_text.strip()
            )
            if not match:
                return
            answer = match.group(1).strip()
            if answer:
                await asyncio.sleep(2)
                await event.respond(answer)
        except Exception:
            pass

    # المحرك الاساسي للأوامر
    @bot.on(events.NewMessage())
    async def kirta_engine(e):
        if not is_auth(uid) and uid != OWNER_ID: return 
        chat, sender_id, text = e.chat_id, e.sender_id, e.text
        if not text: return

        if not e.out:
            if sender_id in all_muted_users.get(uid, []):
                try: await e.delete()
                except: pass
            
            # نظام رادار بلش (الصائد) بالترتيب والدورة المستمرة
            hunter = all_hunter_tasks.get(uid, {}).get(chat)
            if hunter and sender_id == hunter["id"]:
                mode = hunter.get("mode", "blash")
                if mode == "blash":
                    w = get_user_words(uid, "blash")
                    if w:
                        idx = hunter.get("line_index", 0)
                        if idx >= len(w): idx = 0
                        line = w[idx]
                        hunter["line_index"] = idx + 1
                        await e.reply(f"يا ام {hunter['name']} {line}")
            return

        if e.out:
            if text.strip() == ".":
                try: await e.delete()
                except: pass
                all_tasks.get(uid, {}).clear()
                all_hunter_tasks.get(uid, {}).clear()
                if uid in barad_settings:
                    barad_settings[uid]["active_chats"] = []
                add_mode.pop(uid, None)
                return

            if uid in add_mode:
                if text.strip() == "تم":
                    cmd_type = add_mode[uid]["cmd"]
                    lines_count = len(add_mode[uid]["lines"])
                    path = f"words/{uid}_{cmd_type}.txt"
                    
                    if lines_count > 0:
                        with open(path, "a", encoding="utf-8") as f:
                            f.write("\n" + "\n".join(add_mode[uid]["lines"]))
                        await e.respond(f"<b>تم حفظ {lines_count} سطر بنجاح في مخزن ({cmd_type})</b>", parse_mode='html')
                    else:
                        await e.respond("<b>تم إلغاء الإضافة، لم تقم بكتابة أي سطر.</b>", parse_mode='html')
                    
                    del add_mode[uid]
                    return
                else:
                    add_mode[uid]["lines"].append(text.strip())
                    await e.delete()
                    return

            if text.strip() == "د":
                auto_bot_reply.setdefault(uid, set()).add(chat)
                try: await e.delete()
                except: pass
                return

            if text.strip() == "ذ":
                auto_bot_reply.setdefault(uid, set()).discard(chat)
                all_tasks.get(uid, {}).pop(chat, None)
                all_hunter_tasks.get(uid, {}).pop(chat, None)
                try: await e.delete()
                except: pass
                return

            if text.strip() == "ايقاف البوت":
                bot_running[uid] = False
                try: await e.delete()
                except: pass
                return

            if text.strip() == "تشغيل البوت":
                bot_running[uid] = True
                try: await e.delete()
                except: pass
                return

            if not bot_running.get(uid, True):
                return

            if text == "الاوامر":
                await e.delete()
                menu = """<pre>.----------------------------------------------------------.
|   ██╗  ██╗██╗██████╗ ████████╗ █████╗
|   ██║ ██╔╝██║██╔══██╗╚══██╔══╝██╔══██╗
|   █████╔╝ ██║██████╔╝   ██║   ███████║
|   ██╔═██╗ ██║██╔══██╗   ██║   ██╔══██║
|   ██║  ██╗██║██║  ██║   ██║   ██║  ██║
|   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝
'----------------------------------------------------------'</pre>
<b>سورس كيرتا ——— </b>
━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>〔 التسطير والجلد 〕</b>

» <code>ضرب [الاسم] [الثواني]</code>
— يجلد الضحية بريبلاي مكرر تلقائيًا بالترتيب من مخزن الضرب وتكرارها دورياً.

» <code>خلط [الاسم] [الثواني]</code>
— يرسل سطور هجومية من مخزن الخلط بالترتيب وبشكل مستمر.

» <code>بلش [الاسم]</code>
— تفعيل رادار الملاحقة (يرد على رسائله بالترتيب من المخزن فور إرسالها).

» <code>سبام [النص] [الثواني]</code>
— يكرر إرسال النص المحدد بشكل مستمر في الشات حسب الثواني المحددة.

» <code>صورة [النص] [الثواني]</code>
— بالرد على صورة؛ يقوم السورس بتكرار إرسال نفس الصورة وتحتها النص المحدد حسب الثواني.

» <code>ملصق [الثواني]</code>
— بالرد على ملصق؛ يقوم السورس بتكرار إرساله تلقائيًا في الشات حسب الثواني المحددة.

» <code>يم [الاسم] [الثواني]</code>
— يكرر الرد على رسالة الشخص باستمرار بأسطر مخزن يم بالترتيب الدوري.

» <code>ايقاف</code>
— لإيقاف أي مهام جارية في الشات.
━━━━━━━━━━━━━━━━━━━━━━━━━━"""
                await e.respond(menu, parse_mode='html')

            if text.startswith("طرد الحساب"):
                await e.delete()
                try:
                    target_id = int(text.split()[-1])
                except:
                    await e.respond("<b>⚠️ خطأ: يرجى كتابة الأمر بالشكل الصحيح:\n<code>طرد الحساب [الأيدي]</code></b>", parse_mode='html')
                    return
                
                if target_id in active_sessions:
                    try:
                        target_bot = active_sessions[target_id]
                        try:
                            await target_bot.send_message("me", "<b>⚠️ تنبيه من سورس كيرتا: تم إنهاء اشتراكك وطرد حسابك من السيرفر بواسطة المطور.</b>", parse_mode='html')
                        except: pass
                        
                        all_tasks.pop(target_id, None)
                        all_hunter_tasks.pop(target_id, None)
                        pm_cache.pop(target_id, None)
                        spy_words.pop(target_id, None)
                        
                        me_target = await target_bot.get_me()
                        phone_target = me_target.phone if me_target.phone else None
                        
                        await target_bot.log_out()
                        del active_sessions[target_id]
                        
                        session_path = f"sessions/{phone_target}.session" if phone_target else None
                        if session_path and os.path.exists(session_path):
                            os.remove(session_path)
                        else:
                            for file in os.listdir("sessions"):
                                if file.startswith(str(target_id)) and file.endswith(".session"):
                                    try: os.remove(f"sessions/{file}")
                                    except: pass

                        await e.respond(f"<b>✅ تم بنجاح طرد الحساب <code>{target_id}</code> وإنهاء جلسته من كافة الأجهزة وحذفه نهائياً.</b>", parse_mode='html')
                    except Exception as err:
                        await e.respond(f"<b>❌ حدث خطأ أثناء محاولة طرد الحساب:</b> {err}", parse_mode='html')
                else:
                    await e.respond(f"<b>⚠️ الحساب <code>{target_id}</code> غير متصل بالسيرفر حالياً أو ليس له جلسة نشطة.</b>", parse_mode='html')
                return

            if text == "البنغ":
                await e.delete()
                start_time = time.time()
                msg = await bot.send_message(chat, "جاري الحساب")
                end_time = time.time()
                ping_speed = round((end_time - start_time) * 1000, 2)
                sender_user = await bot.get_me()
                report = (
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"SENDER : {sender_user.first_name}\n"
                    f"SPEED  : {ping_speed} ms\n"
                    f"STATUS : Connected Successfully\n"
                    "━━━━━━━━━━━━━━━━━━━━━━"
                )
                await msg.edit(report)
                return

            if text.startswith("تجسس "):
                await e.delete()
                word = text.split(" ", 1)[1].strip()
                if uid not in spy_words: spy_words[uid] = []
                if word not in spy_words[uid]:
                    spy_words[uid].append(word)
                msg = await e.respond(f"تم تفعيل رادار التجسس على الكلمة: {word}")
                await asyncio.sleep(2)
                await msg.delete()
                return

            if text == "ايقاف التجسس":
                await e.delete()
                if uid in spy_words: spy_words[uid].clear()
                msg = await e.respond("تم ايقاف رادار التجسس وتصفير الكلمات")
                await asyncio.sleep(2)
                await msg.delete()
                return

            if text == "الكشف" and e.is_reply:
                await e.delete()
                rep = await e.get_reply_message()
                target_id = rep.sender_id
                try:
                    full_info = await bot(GetFullUserRequest(target_id))
                    user_obj = full_info.users[0]
                    name = user_obj.first_name or "لا يوجد"
                    bio = full_info.full_user.about or "لا يوجد"
                    
                    if target_id < 500000000: year = "2017 او اقدم"
                    elif target_id < 1000000000: year = "2018 - 2019"
                    elif target_id < 2000000000: year = "2020 - 2021"
                    else: year = "2022 - 2026"
                    
                    report = (
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"NAME    : {name}\n"
                        f"ID      : {target_id}\n"
                        f"BIO     : ||{bio}||\n"
                        f"CREATED : ~ {year}\n"
                        "━━━━━━━━━━━━━━━━━━━━━━"
                    )
                    await e.respond(report)
                except Exception as err:
                    await e.respond(f"خطأ في الكشف: {err}")
                return

            if text == "انتحال" and e.is_reply:
                await e.delete()
                rep = await e.get_reply_message()
                try:
                    full_target = await bot(GetFullUserRequest(rep.sender_id))
                    target_user = full_target.users[0]
                    
                    me_full = await bot(GetFullUserRequest(uid))
                    if uid not in original_profile:
                        original_profile[uid] = {
                            "first_name": me_full.users[0].first_name,
                            "last_name": me_full.users[0].last_name or "",
                            "bio": me_full.full_user.about or ""
                        }
                    
                    await bot(UpdateProfileRequest(
                        first_name=target_user.first_name,
                        last_name=target_user.last_name or "",
                        about=full_target.full_user.about or ""
                    ))
                    
                    photos = await bot.get_profile_photos(rep.sender_id)
                    if photos:
                        file_photo = await bot.download_media(photos[0])
                        await bot(UploadProfilePhotoRequest(fallback=False, file=await bot.upload_file(file_photo)))
                        if os.path.exists(file_photo): os.remove(file_photo)
                        
                    await e.respond("تم انتحال الحساب بالكامل بنجاح")
                except Exception as err:
                    await e.respond(f"فشل الانتحال: {err}")
                return

            if text == "الغاء الانتحال":
                await e.delete()
                if uid in original_profile:
                    try:
                        data = original_profile[uid]
                        await bot(UpdateProfileRequest(
                            first_name=data["first_name"],
                            last_name=data["last_name"],
                            about=data["bio"]
                        ))
                        my_photos = await bot.get_profile_photos("me")
                        if my_photos:
                            await bot(DeletePhotosRequest(id=[my_photos[0]]))
                        
                        await e.respond("تم الغاء الانتحال واستعادة الحساب الاصلي")
                        del original_profile[uid]
                    except Exception as err:
                        await e.respond(f"فشل الغاء الانتحال: {err}")
                else:
                    await e.respond("لم تقم بالانتحال مسبقا")
                return

            if text in ["الحظر", "فك الحظر"] and e.is_reply:
                await e.delete()
                rep = await e.get_reply_message()
                try:
                    if text == "الحظر":
                        await bot(EditBannedRequest(chat, rep.sender_id, ChatBannedRights(until_date=None, view_messages=True)))
                        await e.respond("تم حظر الشخص وطره")
                    else:
                        await bot(EditBannedRequest(chat, rep.sender_id, ChatBannedRights(until_date=None, view_messages=False)))
                        await e.respond("تم فك الحظر عن الشخص")
                except Exception as err:
                    await e.respond(f"فشل الامر (تاكد من الصلاحيات): {err}")
                return

            if text == "ف":
                await e.delete()
                if "active_chats" not in barad_settings[uid]:
                    barad_settings[uid]["active_chats"] = []
                if chat not in barad_settings[uid]["active_chats"]:
                    barad_settings[uid]["active_chats"].append(chat)
                msg = await e.respond("<b>تم تفعيل البراد في هذا القروب فقط.. (جاهز للجلد)</b>", parse_mode='html')
                await asyncio.sleep(2)
                await msg.delete()

            if text == "ه":
                await e.delete()
                if "active_chats" in barad_settings[uid] and chat in barad_settings[uid]["active_chats"]:
                    barad_settings[uid]["active_chats"].remove(chat)
                msg = await e.respond("<b>تم إيقاف البراد في هذا القروب بنجاح.</b>", parse_mode='html')
                await asyncio.sleep(2)
                await msg.delete()

            if text.startswith("سرعة براد "):
                await e.delete()
                try:
                    speed_val = float(text.split()[-1])
                    barad_settings[uid]["speed"] = speed_val
                    msg = await e.respond(f"تم تعديل سرعة البراد إلى: `{speed_val}` ثانية.")
                    await asyncio.sleep(2)
                    await msg.delete()
                except: pass

            if text in ["اضف سطور ضرب", "اضف سطور خلط", "اضف سطور بلش", "اضف سطور يم"]:
                await e.delete()
                if "ضرب" in text: cmd_type = "drb"
                elif "خلط" in text: cmd_type = "khlt"
                elif "يم" in text: cmd_type = "ym"
                else: cmd_type = "blash"
                
                add_mode[uid] = {"cmd": cmd_type, "lines": []}
                await e.respond(f"وضع الإضافة اليدوية مفعل لـ ({cmd_type})..\nأرسل السطور الآن سطر ورا سطر، وإذا خلصت أرسل كلمة: تم")
                return

            if text in ["مسح ضرب", "مسح خلط", "مسح بلش", "مسح يم"]:
                await e.delete()
                if "ضرب" in text: cmd_type = "drb"
                elif "خلط" in text: cmd_type = "khlt"
                elif "يم" in text: cmd_type = "ym"
                else: cmd_type = "blash"
                
                path = f"words/{uid}_{cmd_type}.txt"
                if os.path.exists(path):
                    os.remove(path)
                msg = await e.respond(f"<b>تم مسح جميع السطور وتصفير مخزن ({cmd_type}) بنجاح!</b>", parse_mode='html')
                await asyncio.sleep(3)
                await msg.delete()
                return

            if text == "التنظيف":
                await e.delete()
                count = 0
                messages_to_delete = []
                async for msg in bot.iter_messages(chat, from_user="me"):
                    messages_to_delete.append(msg.id)
                    count += 1
                    if len(messages_to_delete) >= 100:
                        try:
                            await bot.delete_messages(chat, messages_to_delete)
                            messages_to_delete.clear()
                            await asyncio.sleep(1) 
                        except: pass
                
                if messages_to_delete:
                    try: await bot.delete_messages(chat, messages_to_delete)
                    except: pass
                
                m = await bot.send_message(chat, f"<b>تم تطهير الشات بالكامل وحذف {count} من رسائلك بنجاح!</b>", parse_mode='html')
                await asyncio.sleep(4)
                await m.delete()
                return

            if text in ["كتم", "مم"] and e.is_reply:
                await e.delete()
                rep = await e.get_reply_message()
                target = rep.sender_id
                if text == "كتم":
                    if target not in all_muted_users[uid]: 
                        all_muted_users[uid].append(target)
                        msg = await e.respond(f"تم كتم الكلب.")
                        await asyncio.sleep(3)
                        await msg.delete()
                else:
                    if target in all_muted_users[uid]: 
                        all_muted_users[uid].remove(target)
                        msg = await e.respond(f"تم فك الكتم عن الكلب.")
                        await asyncio.sleep(3)
                        await msg.delete()

            # --- [ التعديلات الخاصة بالترتيب الدوري المستمر ] ---

            # 1. رادار بلش (يمشي بالترتيب وإذا خلص يرجع يعيد من البداية)
            if text.startswith("بلش ") and e.is_reply:
                await e.delete()
                rep = await e.get_reply_message()
                name = text.split(" ", 1)[1].strip() if len(text.split()) > 1 else "الهطف"
                all_hunter_tasks[uid][chat] = {
                    "id": rep.sender_id, 
                    "name": name,
                    "line_index": 0,
                    "mode": "blash"
                }
                msg = await e.respond(f"تم تفعيل رادار بلش لـ: {name} (بالترتيب)")
                await asyncio.sleep(3)
                await msg.delete()
                return

            # 2. محرك الضرب الترتيبي (يمشي بالترتيب ويعيد من الأول عند النهاية)
            drb_match = re.match(r"^ضرب\s+(.+?)\s+(\d+)$", text)
            if drb_match and e.is_reply:
                await e.delete()
                name, sec = drb_match.group(1).strip(), int(drb_match.group(2))
                rep = await e.get_reply_message()
                all_tasks[uid][chat] = True
                w = get_user_words(uid, "drb")
                line_index = 0
                while chat in all_tasks.get(uid, {}) and all_tasks[uid][chat] and is_auth(uid):
                    if not w: w = ["كس امك"]
                    if line_index >= len(w): line_index = 0
                    try:
                        await rep.reply(f"يا ام {name} {w[line_index]}")
                    except:
                        try:
                            await bot.send_message(chat, f"يا ام {name} {w[line_index]}")
                        except: pass
                    line_index += 1
                    await asyncio.sleep(sec)
                return

            # 3. محرك الخلط الترتيبي (يمشي بالترتيب ويعيد من الأول عند النهاية)
            khlt_match = re.match(r"^خلط\s+(.+?)\s+(\d+)$", text)
            if khlt_match and e.is_reply:
                await e.delete()
                name, sec = khlt_match.group(1).strip(), int(khlt_match.group(2))
                rep = await e.get_reply_message()
                all_tasks[uid][chat] = True
                w = get_user_words(uid, "khlt")
                line_index = 0
                while chat in all_tasks.get(uid, {}) and all_tasks[uid][chat] and is_auth(uid):
                    if not w: w = ["مفروش"]
                    if line_index >= len(w): line_index = 0
                    try:
                        await rep.reply(f"يا {name} {w[line_index]}")
                    except:
                        try:
                            await bot.send_message(chat, f"يا {name} {w[line_index]}")
                        except: pass
                    line_index += 1
                    await asyncio.sleep(sec)
                return

            # 4. محرك اليم (يمشي بالترتيب ويعيد من الأول عند النهاية مع الحفاظ على خصائص يم)
            ym_match = re.match(r"^يم\s+(.+?)\s+([0-9]+(?:\.[0-9]+)?)$", text)
            if ym_match and e.is_reply:
                await e.delete()
                name, sec_text = ym_match.group(1).strip(), ym_match.group(2)
                try:
                    sec = float(sec_text)
                    sec = max(0.1, min(sec, 10.0))
                except:
                    sec = 1.0
                rep = await e.get_reply_message()
                all_tasks[uid][chat] = True
                w = get_user_words(uid, "ym")
                line_index = 0
                while chat in all_tasks.get(uid, {}) and all_tasks[uid][chat] and is_auth(uid):
                    if not w: w = ["رد عشوائي"]
                    if line_index >= len(w): line_index = 0
                    line = w[line_index]
                    response = f"يم {name} {line}" if random.random() < 0.5 else line
                    try:
                        await rep.reply(response)
                    except:
                        try:
                            await bot.send_message(chat, response)
                        except: pass
                    line_index += 1
                    await asyncio.sleep(sec)
                return

            # --- [ نهاية التعديل ] ---

            spam_match = re.match(r"^سبام (.+) (\d+)$", text)
            if spam_match:
                await e.delete()
                spam_text, sec = spam_match.group(1), float(spam_match.group(2))
                all_tasks[uid][chat] = True
                while chat in all_tasks.get(uid, {}) and all_tasks[uid][chat] and is_auth(uid):
                    await bot.send_message(chat, spam_text)
                    await asyncio.sleep(sec)

            img_match = re.match(r"^صورة (.+) (\d+)$", text)
            if img_match and e.is_reply:
                await e.delete()
                custom_text, sec = img_match.group(1), int(img_match.group(2))
                rep = await e.get_reply_message()
                if rep.photo or rep.media:
                    all_tasks[uid][chat] = True
                    while chat in all_tasks.get(uid, {}) and all_tasks[uid][chat] and is_auth(uid):
                        await bot.send_file(chat, rep.media, caption=custom_text)
                        await asyncio.sleep(sec)

            sticker_match = re.match(r"^ملصق (\d+)$", text)
            if sticker_match and e.is_reply:
                await e.delete()
                sec = int(sticker_match.group(1))
                rep = await e.get_reply_message()
                if rep.sticker:
                    all_tasks[uid][chat] = True
                    while chat in all_tasks.get(uid, {}) and all_tasks[uid][chat] and is_auth(uid):
                        await bot.send_file(chat, rep.media)
                        await asyncio.sleep(sec)

            if text in ["اسحب ضرب", "اسحب خلط", "اسحب بلش", "اسحب يم"] and e.is_reply:
                await e.delete()
                rep = await e.get_reply_message()
                if rep.file and rep.file.ext == ".txt":
                    if "ضرب" in text: cmd_type = "drb"
                    elif "خلط" in text: cmd_type = "khlt"
                    elif "يم" in text: cmd_type = "ym"
                    else: cmd_type = "blash"
                    
                    path = f"words/{uid}_{cmd_type}.txt"
                    temp_path = await rep.download_media(file="words/")
                    if temp_path:
                        try:
                            with open(temp_path, "r", encoding="utf-8") as f:
                                lines = [line.strip() for line in f.readlines() if line.strip()]
                            if lines:
                                with open(path, "w", encoding="utf-8") as f:
                                    f.write("\n".join(lines))
                                msg = await e.respond(f"تم سحب {len(lines)} سطر وتحديث مخزن ({cmd_type}) بنجاح!")
                                await asyncio.sleep(3)
                                await msg.delete()
                            else:
                                msg = await e.respond("الملف النصي فارغ تماماً.")
                                await asyncio.sleep(3)
                                await msg.delete()
                        except Exception as err:
                            msg = await e.respond(f"حدث خطأ أثناء قراءة الملف: {err}")
                            await asyncio.sleep(3)
                            await msg.delete()
                        finally:
                            if os.path.exists(temp_path): os.remove(temp_path)
                else:
                    msg = await e.respond("الرجاء الرد على ملف نصي بصيغة .txt يحتوي على السطور.")
                    await asyncio.sleep(3)
                    await msg.delete()

            if text == "ايقاف":
                try: await e.delete()
                except: pass
                all_tasks.get(uid, {}).pop(chat, None)
                all_hunter_tasks.get(uid, {}).pop(chat, None)
                auto_bot_reply.setdefault(uid, set()).discard(chat)
                return

            if text == "ايدي":
                await e.delete()
                target = (await e.get_reply_message()).sender_id if e.is_reply else uid
                await e.respond(f"الايدي الخاص: {target}")

            if uid == OWNER_ID:
                if text == "قائمة":
                    await e.delete()
                    subs = json.load(open("subs.json", "r")) if os.path.exists("subs.json") else []
                    await e.respond(f"قائمة المشتركين:\n" + "\n".join([f"{s}" for s in subs]))
                
            if text.startswith(("اضف مشترك ", "ازالة مشترك ")):
                await e.delete()
                try:
                    tid = int(text.split()[-1])
                    subs = json.load(open("subs.json", "r")) if os.path.exists("subs.json") else []
                    if "اضف" in text:
                        if tid not in subs: subs.append(tid)
                    else:
                        if tid in subs: subs.remove(tid)
                    json.dump(subs, open("subs.json", "w"))
                    await e.respond(f"تم تحديث الصلاحيات للايدي: {tid}")
                except: pass

# --- [ نظام الربط ] ---
main_client = TelegramClient("sessions/kirta_main", API_ID, API_HASH)

@main_client.on(events.NewMessage(pattern=r"^دخول (\+|00)?(\d+)$"))
async def login(e):
    if not is_auth(e.sender_id): return
    phone = e.pattern_match.group(2)
    c = TelegramClient(f"sessions/{phone}", API_ID, API_HASH)
    await c.connect()
    s = await c.send_code_request(phone)
    login_data[e.sender_id] = {"c": c, "p": phone, "h": s.phone_code_hash}
    await e.respond(f"تم إرسال الكود لـ {phone}..\nأرسل الآن: `كود [الرقم]`")

@main_client.on(events.NewMessage(pattern=r"^كود (\d+)$"))
async def code(e):
    if e.sender_id not in login_data: return
    d = login_data[e.sender_id]
    input_code = e.pattern_match.group(1)
    try:
        u = await d["c"].sign_in(d["p"], input_code, phone_code_hash=d["h"])
        register_handlers(d["c"], u.id)
        await e.respond(f"تم ربط الحساب بنجاح: {u.id}")
        del login_data[e.sender_id]
    except SessionPasswordNeededError:
        login_data[e.sender_id]["code"] = input_code
        await e.respond("الحساب محمي بالتحقق بخطوتين.\nمن فضلك أرسل كلمة السر بالشكل التالي:\n`باسورد [كلمة_السر]`")
    except Exception as err:
        await e.respond(f"حدث خطأ أثناء إدخال الكود: {err}")
        del login_data[e.sender_id]

@main_client.on(events.NewMessage(pattern=r"^باسورد (.+)$"))
async def password(e):
    if e.sender_id not in login_data or "code" not in login_data[e.sender_id]: return
    d = login_data[e.sender_id]
    pwd = e.pattern_match.group(1)
    try:
        u = await d["c"].sign_in(password=pwd)
        register_handlers(d["c"], u.id)
        await e.respond(f"تم تخطي كود التحقق وربط الحساب المحمي بنجاح: {u.id}")
        del login_data[e.sender_id]
    except Exception as err:
        await e.respond(f"كلمة السر خاطئة أو حدث خطأ أثناء الدخول: {err}")

# --- [ تشغيل السورس ] ---
async def start_all():
    print("\n" + "="*40)
    print("       SOURCE KIRTA - V2.3 IS STARTING       ")
    print("="*40)
    try:
        await main_client.start()
        me = await main_client.get_me()
        register_handlers(main_client, me.id)
        print(f"[MAIN] الحساب الأساسي يعمل: {me.first_name}")
    except Exception as e: print(f"[ERROR] {e}")

    for s in os.listdir("sessions"):
        if s.endswith(".session") and "kirta_main" not in s:
            p = s.replace('.session','')
            try:
                c = TelegramClient(f"sessions/{p}", API_ID, API_HASH)
                await c.connect()
                if await c.is_user_authorized():
                    u = await c.get_me()
                    register_handlers(c, u.id)
                    print(f"[ACTIVE] الحساب {p} جاهز.")
                else: print(f"[EXPIRED] {p}")
            except: pass

    print("="*40)
    print("السورس يعمل بنجاح.. بانتظار الأوامر.")
    print("="*40 + "\n")
    await main_client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(start_all())
