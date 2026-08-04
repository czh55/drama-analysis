#!/usr/bin/env python3
"""为问心2 e01 的关键台词补充英文翻译（样板集）。"""
import json
from pathlib import Path

P = Path("/tmp/wenxin2-trans/content-e01.json")

# {中文原文: 英文翻译}
EN = {
    "「林主任真是鬼门关前的巧人。」": '"Director Lin is truly a magician at the gates of death."',
    "「这个月奶茶没少喝呀，今天都第二杯了。」": '"You\'ve been drinking a lot of milk tea this month—this is already the second cup today."',
    "「林主任，心内的人呢？」「再等一会儿。」": '"Director Lin, where are the cardiology doctors?" "Just wait a little longer."',
    "「要尊重科学，更要把病人放在第一位，我一直都记住这句话。」": '"Respect science, and put patients first—I\'ve always kept that in mind."',
    "「不管是看病救人也好，或者协助当地培养一批新人也好，我都想去做点什么。」": '"Whether it\'s treating patients or helping train new doctors locally, I want to do something."',
    "「咱们这支队伍恐怕得藏器藏一会儿，这叫各自磨刀，等你回来，收刀入鞘。」": '"Our team will have to keep its tools sheathed for now. We each sharpen our blades, and when you come back, we put them away together."',
    "「雪妹，放松，师父马上到，你坚持一下！」": '"Xuemei, relax—your doctor is on the way. Hang in there!"',
    "「考虑到雪妹怀着宝宝，我们不能忽视射线的伤害。」": '"Given that Xuemei is pregnant, we can\'t ignore the harm from radiation."',
    "「我打算给她进行一个内外科结合的复合手术。」": '"I plan to perform a combined surgery involving both internal medicine and surgery on her."',
    "「既避免了对胎儿的射线伤害，也规避掉了体外循环所带来的风险。」": '"This avoids radiation harm to the fetus and eliminates the risks of cardiopulmonary bypass."',
    "「这就是心脏中心的刀尖队。」": '"This is the tip-of-the-knife team of the Heart Center."',
    "「你带回来的病人，长命百岁。」": '"The patient you brought back—may she live a long and healthy life."',
    "「为什么提前回来不说一声，搞突然袭击？」「就想给你个惊喜吗？」": '"Why did you come back early without telling anyone—a surprise attack?" "Just wanted to surprise you!"',
    "「Family Day，一周一家人聚一次！」": '"Family Day—the whole family gathers once a week!"',
    "「这可不是一般的方便面，我们可有贵州特产。」": '"This isn\'t just any instant noodles—we\'ve got authentic Guizhou specialties here."',
    "「我现在回来，就是不想参加这次心内科主任的竞选。」": '"I came back now precisely because I don\'t want to run for the director of cardiology."',
    "「我们医院的周筱风主任，也在其中。」": '"Our hospital\'s Director Zhou Xiaofeng is also among them."',
    "「欢迎周筱风主任的正式回归，我回来了。」": '"Let\'s welcome Director Zhou Xiaofeng\'s official return—I\'m back."',
    "「双绒双羊，两个宝宝都在各自独立的房间里。」": '"Dichorionic diamniotic—each baby is in its own separate sac."',
    "「大部分家庭会选择减胎，这样你还能保留一个健康的孩子。」": '"Most families choose selective reduction, so you can still keep a healthy child."',
    "「他现在还活着，他肯定是有办法的！所以你帮我想想办法。」": '"He\'s still alive—there must be a way! Please, think of something for me."',
    "「宫内介入治疗，给孩子做微创手术，把肺动脉打开，就有希望让心脏得到发育。」": '"Intrauterine intervention—a minimally invasive procedure to open the baby\'s pulmonary artery, giving the heart a chance to develop."',
    "「我不怕风险的，我真的不怕风险的！」": '"I\'m not afraid of the risks—I really am not!"',
    "「我不想失去这个娃娃，我要救她。」": '"I don\'t want to lose this baby—I want to save her."',
    "「我就觉得她好像从来没有离开过我，一直就在我身边一样。」": '"I feel like she has never really left me, like she\'s always been right by my side."',
    "「别的人不要她，但我不能不要她。」": '"Other people may give up on her, but I can\'t."',
    "「我求求你，求求你能救救她和我。」": '"Please, I beg you—save her and me."',
    "「万一出了问题，有了医疗纠纷，那对你的竞聘是非常不利的。」": '"If anything goes wrong and there\'s a medical dispute, it will seriously hurt your candidacy."',
    "「就算有影响，我也还是想试试看。」": '"Even if it has consequences, I still want to try."',
    "「这一次的心跳，从来不曾示弱。」": '"This heartbeat has never once shown weakness."',
}

content = json.loads(P.read_text(encoding="utf-8"))

updated = 0
missing = []
for scene in content["scenes"]:
    new_quotes = []
    for q in scene["quotes"]:
        if isinstance(q, dict):
            new_quotes.append(q)
            continue
        en = EN.get(q)
        if not en:
            missing.append(f"{scene['id']}: {q}")
            new_quotes.append(q)
            continue
        new_quotes.append({"zh": q, "en": en})
        updated += 1
    scene["quotes"] = new_quotes

P.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"更新 {updated} 条台词")
if missing:
    print("缺失翻译:")
    for m in missing:
        print(" ", m)
