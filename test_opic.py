import json
import random
import pandas as pd
import sys
sys.stdout.reconfigure(encoding="utf-8")

# ==============================
# 1. Fake Dataset (Topics + Prompts)
# ==============================

TOPICS = [
    {"topic_id":"prof_job_office","category":"profile","option_label":"Company/office worker"},
    {"topic_id":"ft_movies_cinema","category":"free_time","option_label":"Watching movies (at cinema)"},
    {"topic_id":"ft_beach","category":"free_time","option_label":"Going to the beach"},
    {"topic_id":"ft_park","category":"free_time","option_label":"Going to a Park"},
    {"topic_id":"hb_cooking","category":"hobbies","option_label":"Cooking"},
    {"topic_id":"hb_pets","category":"hobbies","option_label":"Raising pets"},
    {"topic_id":"hb_painting","category":"hobbies","option_label":"Painting / Drawing"},
    {"topic_id":"sp_walking","category":"sports","option_label":"Walking"},
    {"topic_id":"sp_badminton","category":"sports","option_label":"Badminton"},
    {"topic_id":"sp_swimming","category":"sports","option_label":"Swimming"},
    {"topic_id":"tr_overseas_trip","category":"travel","option_label":"Overseas trip"},
    {"topic_id":"tr_staycation","category":"travel","option_label":"No traveling (Staycation)"},
]

PROMPTS = [
    # Movies
    {"template_id":"q_ft_movies_im_1","topic_id":"ft_movies_cinema","level":"IM","mode":"narrative","prompt_text":"Talk about the last time you watched a movie at a cinema."},
    {"template_id":"q_ft_movies_ih_1","topic_id":"ft_movies_cinema","level":"IH","mode":"narrative","prompt_text":"Describe a memorable cinema experience and why it was special."},
    {"template_id":"q_ft_movies_al_1","topic_id":"ft_movies_cinema","level":"AL","mode":"compare","prompt_text":"Compare watching movies at a cinema and at home."},

    # Travel
    {"template_id":"q_tr_overseas_im_1","topic_id":"tr_overseas_trip","level":"IM","mode":"narrative","prompt_text":"Tell me about an overseas trip you have taken."},
    {"template_id":"q_tr_overseas_ih_1","topic_id":"tr_overseas_trip","level":"IH","mode":"narrative","prompt_text":"Describe a challenge you faced during an overseas trip."},
    {"template_id":"q_tr_overseas_al_1","topic_id":"tr_overseas_trip","level":"AL","mode":"roleplay","prompt_text":"(Role-play) Call a hotel to change your reservation dates."},

    # Cooking
    {"template_id":"q_hb_cook_im_1","topic_id":"hb_cooking","level":"IM","mode":"process","prompt_text":"Describe how to cook a simple dish you like."},
    {"template_id":"q_hb_cook_ih_1","topic_id":"hb_cooking","level":"IH","mode":"narrative","prompt_text":"Tell a story about a time you cooked for others."},
    {"template_id":"q_hb_cook_al_1","topic_id":"hb_cooking","level":"AL","mode":"explain","prompt_text":"Explain how your cooking preferences have changed over time."},

    # Pets
    {"template_id":"q_hb_pets_im_1","topic_id":"hb_pets","level":"IM","mode":"narrative","prompt_text":"Talk about a pet you have or would like to have."},
    {"template_id":"q_hb_pets_ih_1","topic_id":"hb_pets","level":"IH","mode":"explain","prompt_text":"Explain the responsibilities of raising a pet."},
    {"template_id":"q_hb_pets_al_1","topic_id":"hb_pets","level":"AL","mode":"roleplay","prompt_text":"(Role-play) Call a vet to describe your pet's symptoms."},
]

# ==============================
# 2. Exam Generator Class
# ==============================

class OPIcExamGenerator:
    def __init__(self, topics, prompts, rng_seed=None):
        self.topics = topics
        self.prompts = prompts
        if rng_seed:
            random.seed(rng_seed)

    def generate_exam(
        self,
        selected_topic_ids,
        level: str,
        n_questions: int = 12,
        ensure_modes=None,
        lang: str | None = None,
    ):
        ensure_modes = ensure_modes or []
        level = level.upper()

        # ---- 1) Build pools ----
        def match_lang(pool):
            if lang:
                pool = [p for p in pool if p.get("lang") == lang]
            else:
                pref_en = [p for p in pool if p.get("lang") == "en"]
                pool = pref_en or pool
            return pool

        pools_by_topic = {}
        for tid in selected_topic_ids:
            pool = [p for p in self.prompts if p["topic_id"] == tid and p["level"] == level]
            pool = match_lang(pool)
            if pool:
                pools_by_topic[tid] = pool[:]  # copy

        # Nếu không có topic nào còn prompt hợp lệ, sẽ backfill toàn bộ
        rr_topics = list(pools_by_topic.keys())
        random.shuffle(rr_topics)

        chosen = []
        used_ids = set()
        used_modes = set()

        # ---- 2) Round-robin w/ progress check ----
        while len(chosen) < n_questions and rr_topics:
            progress = False
            # duyệt 1 vòng
            for tid in rr_topics[:]:  # copy vì có thể remove
                pool = pools_by_topic.get(tid, [])
                if not pool:
                    rr_topics.remove(tid)
                    continue

                # ưu tiên mode còn thiếu
                need_modes = [m for m in ensure_modes if m not in used_modes]
                pick = None
                if need_modes:
                    candidates = [p for p in pool if p.get("mode") in need_modes and p["template_id"] not in used_ids]
                    if candidates:
                        pick = random.choice(candidates)

                if pick is None:
                    # lấy ngẫu nhiên cái chưa dùng
                    candidates = [p for p in pool if p["template_id"] not in used_ids]
                    pick = random.choice(candidates) if candidates else None

                if pick:
                    chosen.append(pick)
                    used_ids.add(pick["template_id"])
                    if pick.get("mode"):
                        used_modes.add(pick["mode"])
                    # remove khỏi pool topic để không lặp
                    pools_by_topic[tid] = [p for p in pool if p["template_id"] != pick["template_id"]]
                    if not pools_by_topic[tid]:
                        rr_topics.remove(tid)
                    progress = True

                if len(chosen) >= n_questions or not rr_topics:
                    break

            # nếu 1 vòng không thêm được gì → thoát để backfill
            if not progress:
                break

        # ---- 3) Backfill nếu còn thiếu ----
        if len(chosen) < n_questions:
            pool_any = [p for p in self.prompts if p["level"] == level and p["template_id"] not in used_ids]
            pool_any = match_lang(pool_any)
            random.shuffle(pool_any)
            for p in pool_any:
                if len(chosen) >= n_questions:
                    break
                chosen.append(p)
                used_ids.add(p["template_id"])
                if p.get("mode"):
                    used_modes.add(p["mode"])

        # ---- 4) Ép ensure_modes bằng thay thế (giới hạn) ----
        missing = [m for m in ensure_modes if m not in used_modes]
        if missing:
            pool_any = [p for p in self.prompts if p["level"] == level and p["template_id"] not in used_ids]
            pool_any = match_lang(pool_any)
            # giới hạn số thay thế để an toàn
            swaps_left = min(len(missing), 5)
            for m in missing:
                if swaps_left <= 0:
                    break
                cands = [p for p in pool_any if p.get("mode") == m]
                if not cands or not chosen:
                    continue
                newq = random.choice(cands)
                # thay ngẫu nhiên 1 câu khác mode (hoặc bất kỳ)
                for _ in range(20):
                    idx = random.randrange(len(chosen))
                    if chosen[idx]["template_id"] != newq["template_id"]:
                        used_ids.discard(chosen[idx]["template_id"])
                        chosen[idx] = newq
                        used_ids.add(newq["template_id"])
                        used_modes.add(m)
                        swaps_left -= 1
                        break

        # ---- 5) Đánh số thứ tự & trả về ----
        exam = []
        for i, p in enumerate(chosen[:n_questions], start=1):
            exam.append({
                "q_no": i,
                "template_id": p["template_id"],
                "topic_id": p["topic_id"],
                "level": p["level"],
                "mode": p.get("mode"),
                "lang": p.get("lang", "en"),
                "prompt_text": p["prompt_text"],
                "time_limit_s": p.get("time_limit_s", 60),
            })
        return exam


# ==============================
# 3. Demo Usage
# ==============================

if __name__ == "__main__":
    generator = OPIcExamGenerator(TOPICS, PROMPTS, rng_seed=42)
    selected_topics = ["prof_job_office","ft_movies_cinema","hb_cooking","hb_pets","tr_overseas_trip"]
    exam = generator.generate_exam(selected_topics, level="AL", n_questions=8, ensure_modes=["narrative","compare","roleplay"])
    
    # In ra kết quả
    for q in exam:
        print(f"Q{q['q_no']} [{q['mode']}]: {q['prompt_text']}")

    # Xuất ra CSV
    pd.DataFrame(exam).to_csv("opic_sample_exam.csv", index=False, encoding="utf-8")
    print("\nĐề thi mẫu đã được lưu vào opic_sample_exam.csv")
