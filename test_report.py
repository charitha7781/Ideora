import json
import report_part as rp
from report_part import build_report
from sample_data import SAMPLE_COMPETITORS as COMP, SAMPLE_SIGNALS as SIG

KEYS = {"summary","competition","customer_feedback","gaps","score","score_reason","sources"}

GOOD = json.dumps({
 "summary":"Three cafes already exist nearby. Students are visiting cafes more.",
 "competition":{"count":0,"average_rating":0,"notes":"Ratings are good, so a new cafe must stand out."},
 "customer_feedback":["Not enough data: no review text was available."],
 "gaps":["Not enough data to find gaps."],
 "score":7, "score_reason":"Demand looks fine, but competition is real.",
 "sources":[{"title":"Example Cafe One","link":"https://example.com/cafe-one"},
            {"title":"News","link":"https://example.com/news-1"},
            {"title":"Fake","link":"https://invented.com"}]})

# the team's list format is split by "type"
sig = rp.normalize_signals(SIG)
assert len(sig["news"])==1 and len(sig["search"])==1 and sig["trends"] is None

# good answer
r = build_report("A student-friendly cafe","near RNS Institute of Technology, Bengaluru",COMP,SIG,
                 ai_call=lambda s,u: "```json\n"+GOOD+"\n```")
assert set(r)==KEYS, set(r)
assert r["competition"]["count"]==3 and r["competition"]["average_rating"]==4.27
assert isinstance(r["score"],int) and len(r["sources"])==2
assert all("invented" not in s["link"] for s in r["sources"])
json.dump(r, open("test_report.json","w"), indent=2, ensure_ascii=False)

# dict-style signals with Google Trends data
trend_sig = {"search":[], "news":[], "trends":{"interest_over_time":{"timeline_data":[
    {"values":[{"extracted_value":v}]} for v in (40,42,45,50,58,70)]}}}
assert rp.compute_trend(trend_sig["trends"])["direction"]=="rising"
assert set(build_report("cafe","B",COMP,trend_sig,ai_call=lambda s,u:GOOD))==KEYS

# retry, fallback, empty
calls=[]
def flaky(s,u):
    calls.append(1); return "sorry" if len(calls)==1 else GOOD
assert set(build_report("cafe","B",COMP,SIG,ai_call=flaky))==KEYS and len(calls)==2
r3 = build_report("cafe","B",COMP,SIG,ai_call=lambda s,u:"nope")
assert set(r3)==KEYS and 1<=r3["score"]<=10
assert set(build_report("cafe","B",[],[],ai_call=lambda s,u:"nope"))==KEYS

# extras switch
rp.INCLUDE_EXTRAS = True
assert {"risks","market_interest"} <= set(build_report("cafe","B",COMP,SIG,ai_call=lambda s,u:GOOD))
print("ALL TESTS PASSED")