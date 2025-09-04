import os
import re
import time
import nltk
import praw
import pandas as pd
from transformers import pipeline
from comparative_sentiment import postprocess_sentiment_results

# Ensure NLTK punkt is available
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

print("CLOUD PROVIDER SENTIMENT ANALYSIS - PERFORMANCE-FOCUSED (NON-OPTIMIZED)")
print("=" * 70)

# 1) Load BERT model (first run will download the model; that is expected)
print("Loading BERT model...")
start_load = time.time()
try:
    bert_pipeline = pipeline(
        "sentiment-analysis",
        model="nlptown/bert-base-multilingual-uncased-sentiment",
        return_all_scores=True,
    )
    print(f"BERT model loaded in {time.time() - start_load:.1f}s")
except Exception as e:
    print(f"FATAL: Unable to load BERT model: {e}")
    raise SystemExit(1)

# 2) Reddit credentials from environment variables (do NOT hardcode secrets)
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "cloud-analyzer:v1.0 (by u/unknown)")

if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
    print("FATAL: Missing Reddit credentials. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in your environment.")
    raise SystemExit(1)

# 3) Reddit API client
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
)

# 4) Configuration
subreddits = [
    "MachineLearning", "DeepLearning", "learnmachinelearning", "Artificial",
    "LanguageTechnology", "DataScience", "computervision", "MLQuestions",
    "AI_Community", "robotics", "NLP", "BigData", "algorithms", "Cloud", "cloudcomputing"
]

providers = ["AWS", "Azure", "Google Cloud", "GCP", "IBM Cloud", "Amazon Web Services"]

key_areas = {
    "cost": ["cheap", "expensive", "price", "affordable", "pricing", "cost", "pay-as-you-go", "free tier", "discount", "billing"],
    "scalability": ["scalable", "scale", "elastic", "autoscale", "capacity", "grow", "shrink", "dynamic", "load balancing"],
    "security": ["secure", "security", "vulnerable", "encryption", "breach", "compliance", "firewall", "attack", "access control", "IAM"],
    "performance": ["fast", "slow", "latency", "throughput", "speed", "efficient", "optimization", "response time"],
    "support": ["support", "help", "documentation", "customer service", "forum", "ticket", "response", "tutorial"],
}

# Tune this for size/speed
num_posts = 100

# Storage
results = {provider: {area: [] for area in key_areas} for provider in providers}

# Helpers
def get_bert_sentiment(text: str):
    try:
        if len(text) > 512:
            text = text[:512]
        result = bert_pipeline(text)
        if isinstance(result[0], list):
            best = max(result[0], key=lambda x: x["score"])
        else:
            best = result[0]
        label = best["label"]
        score = best["score"]
        if label in ["POSITIVE", "4 stars", "5 stars", "LABEL_2"]:
            return "Positive", score
        elif label in ["NEGATIVE", "1 star", "2 stars", "LABEL_0"]:
            return "Negative", score
        else:
            return "Neutral", score
    except Exception:
        return "Error", 0.0

def contains_whole_word(word: str, text: str):
    pattern = r"\b" + re.escape(word) + r"\b"
    return re.search(pattern, text, re.IGNORECASE) is not None

def extract_relevant_sentences(text: str, provider: str, keywords: list[str]):
    sentences = nltk.sent_tokenize(text or "")
    relevant = []
    for sent in sentences:
        if contains_whole_word(provider, sent) and any(contains_whole_word(kw, sent) for kw in keywords):
            relevant.append(sent)
    return relevant

# Performance counters
total_posts_processed = 0
total_comments_processed = 0
total_sentences_analyzed = 0
total_api_calls = 0
errors_count = 0
performance_log = []

print(f"\nStarting analysis: {len(subreddits)} subreddits × {num_posts} posts")
print(f"Providers: {', '.join(providers)}")
print(f"Aspects: {', '.join(key_areas.keys())}")
print("-" * 70)

overall_start = time.time()

for idx, subreddit_name in enumerate(subreddits, 1):
    sub_start = time.time()
    print(f"[{idx:2d}/{len(subreddits)}] Processing r/{subreddit_name}...", end=" ")
    sub_posts = 0
    sub_comments = 0
    sub_sentences = 0
    sub_errors = 0

    try:
        subreddit = reddit.subreddit(subreddit_name)
        total_api_calls += 1

        for submission in subreddit.new(limit=num_posts):
            sub_posts += 1
            total_posts_processed += 1
            total_api_calls += 1

            main_text = (submission.title or "") + " " + (submission.selftext or "")

            for provider in providers:
                for area, keywords in key_areas.items():
                    relevant = extract_relevant_sentences(main_text, provider, keywords)
                    for sent in relevant:
                        sentiment, conf = get_bert_sentiment(sent)
                        sub_sentences += 1
                        total_sentences_analyzed += 1
                        results[provider][area].append({
                            "sentence": sent,
                            "sentiment": sentiment,
                            "confidence": conf,
                            "source": f"r/{subreddit_name} - Post",
                            "url": submission.url,
                            "provider": provider,
                            "aspect": area,
                        })

            # Comments
            try:
                submission.comments.replace_more(limit=0)
                total_api_calls += 1
                c = 0
                for comment in submission.comments.list():
                    c += 1
                    if c > 25:
                        break
                    sub_comments += 1
                    total_comments_processed += 1
                    body = comment.body or ""
                    for provider in providers:
                        for area, keywords in key_areas.items():
                            relevant = extract_relevant_sentences(body, provider, keywords)
                            for sent in relevant:
                                sentiment, conf = get_bert_sentiment(sent)
                                sub_sentences += 1
                                total_sentences_analyzed += 1
                                results[provider][area].append({
                                    "sentence": sent,
                                    "sentiment": sentiment,
                                    "confidence": conf,
                                    "source": f"r/{subreddit_name} - Comment",
                                    "url": submission.url,
                                    "provider": provider,
                                    "aspect": area,
                                })
            except Exception:
                sub_errors += 1
                errors_count += 1

        sub_time = time.time() - sub_start
        posts_per_sec = sub_posts / sub_time if sub_time > 0 else 0.0
        sents_per_sec = sub_sentences / sub_time if sub_time > 0 else 0.0
        print(f"✓ {sub_time:.1f}s | {sub_posts}p {sub_comments}c {sub_sentences}s | {posts_per_sec:.1f}p/s {sents_per_sec:.1f}s/s")

        performance_log.append({
            "subreddit": subreddit_name,
            "time_sec": sub_time,
            "posts": sub_posts,
            "comments": sub_comments,
            "sentences": sub_sentences,
            "posts_per_sec": posts_per_sec,
            "sentences_per_sec": sents_per_sec,
            "errors": sub_errors,
        })

        if idx % 5 == 0:
            elapsed = time.time() - overall_start
            avg = sum(p["time_sec"] for p in performance_log) / len(performance_log)
            est_remain = (len(subreddits) - idx) * avg
            print(f"    CHECKPOINT: {idx}/{len(subreddits)} | {elapsed:.0f}s elapsed | ~{est_remain:.0f}s remaining")

        time.sleep(0.5)  # gentle pacing for API
    except Exception as e:
        print(f"✗ FAILED: {str(e)[:60]}...")
        errors_count += 1

# Final performance report
total_time = time.time() - overall_start
print("\n" + "=" * 70)
print("PERFORMANCE ANALYSIS COMPLETE")
print("=" * 70)
print(f"Total runtime:           {total_time:.1f}s ({total_time/60:.1f} min)")
print(f"Posts processed:         {total_posts_processed:,}")
print(f"Comments processed:      {total_comments_processed:,}")
print(f"Sentences analyzed:      {total_sentences_analyzed:,}")
print(f"API calls (approx):      {total_api_calls:,}")
print(f"Errors encountered:      {errors_count}")

if total_time > 0 and total_sentences_analyzed > 0:
    print(f"Posts per second:        {total_posts_processed/total_time:.2f}")
    print(f"Sentences per second:    {total_sentences_analyzed/total_time:.2f}")
    print(f"Time per sentence:       {total_time/total_sentences_analyzed:.3f}s")

# Summary export
print("\nExporting CSVs...")
summary_rows = []
for provider in providers:
    for area in key_areas:
        opinions = results[provider][area]
        total = len(opinions)
        if total == 0:
            continue
        pos = sum(1 for op in opinions if op["sentiment"] == "Positive")
        neg = sum(1 for op in opinions if op["sentiment"] == "Negative")
        neu = sum(1 for op in opinions if op["sentiment"] == "Neutral")
        avg_conf = sum(op["confidence"] for op in opinions) / total if total > 0 else 0.0
        summary_rows.append({
            "Provider": provider,
            "Area": area,
            "Total": total,
            "Positive": pos,
            "Negative": neg,
            "Neutral": neu,
            "Pos_Pct": (pos / total) * 100.0,
            "Neg_Pct": (neg / total) * 100.0,
            "Neu_Pct": (neu / total) * 100.0,
            "Avg_Confidence": avg_conf,
        })

df_summary = pd.DataFrame(summary_rows)
if not df_summary.empty:
    df_summary.to_csv("sentiment_analysis_results.csv", index=False)

# Performance log export
df_perf = pd.DataFrame(performance_log)
if not df_perf.empty:
    df_perf.to_csv("performance_metrics.csv", index=False)

# Detailed export
detailed_rows = []
for provider in providers:
    for area in key_areas:
        for op in results[provider][area]:
            detailed_rows.append({
                "Provider": op["provider"],
                "Aspect": op["aspect"],
                "Sentiment": op["sentiment"],
                "Confidence": op["confidence"],
                "Sentence": op["sentence"][:200],
                "Source": op["source"],
                "URL": op["url"],
            })

df_detailed = pd.DataFrame(detailed_rows)
if not df_detailed.empty:
    df_detailed.to_csv("detailed_sentiment_data.csv", index=False)

# Comparative sentiment analysis
print("\nPerforming comparative sentiment analysis...")
comparative_results = postprocess_sentiment_results(results)

# Export comparative analysis results
if comparative_results['comparative_summary'] is not None and not comparative_results['comparative_summary'].empty:
    comparative_results['comparative_summary'].to_csv("comparative_sentiment_analysis.csv", index=False)
    print("✓ Exported comparative_sentiment_analysis.csv")

if comparative_results['comparison_matrix'] is not None and not comparative_results['comparison_matrix'].empty:
    comparative_results['comparison_matrix'].to_csv("provider_sentiment_matrix.csv", index=True)
    print("✓ Exported provider_sentiment_matrix.csv")

# Display comparative insights
print("\n" + "=" * 70)
print("COMPARATIVE SENTIMENT ANALYSIS INSIGHTS")
print("=" * 70)

# Overall provider rankings
overall_rankings = comparative_results['overall_rankings']
if overall_rankings:
    print("\nOVERALL PROVIDER RANKINGS:")
    for i, (provider, score) in enumerate(overall_rankings, 1):
        print(f"{i:2d}. {provider:<20} (Score: {score:+.3f})")

# Aspect-specific insights
insights = comparative_results['insights']
if insights:
    print("\nKEY INSIGHTS:")
    for insight in insights:
        print(f"• {insight}")

# Best/worst providers by aspect
aspect_rankings = comparative_results['aspect_rankings']
if aspect_rankings:
    print("\nBEST PERFORMERS BY ASPECT:")
    for aspect, data in aspect_rankings.items():
        if data['best_provider']:
            best_score = data['provider_scores'][data['best_provider']]['sentiment_score']
            print(f"• {aspect.title():<12}: {data['best_provider']} (Score: {best_score:+.3f})")

print("Done.")
