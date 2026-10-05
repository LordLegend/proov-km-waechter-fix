# What I checked, and what the agent got wrong

## What the agent got wrong

The biggest one was the risk analysis. On the first try Bob picked its own cut-off (0.20 of the range) and then said only km_since_service matters and the other columns are "essentially flat". They are not. Cars that broke down drove 160 km a day against 131, and had a load factor of 0.60 against 0.51. The score Bob built was just km_since_service scaled to 0-100, so it was the 80% rule again. In Bob's own output it caught 15 of the 26 breakdowns and the old rule caught 17. I had it measure the gaps in standard deviations instead, and then all three columns showed up.

Bob also made a new crash while fixing an old one. After the fleet_report fix the average could be None, and print_report() still tried to format it as a number. A fleet where no car has a reading gave a TypeError. There is a test for that now.

In the last analysis table every combined rank was one too high. The ranking list said VOS-1471 is rank 9 and the table right under it said 10. It was an index that got +1 twice.

A few times Bob's report did not match what really happened:

- It listed "average wear" as a failing check when verify.py printed PASS for it.
- It said the km_wachter.py change was already committed. Nothing was committed at that point.
- It ran only one test file (3 of 5 tests) and showed that as the pytest run.
- I asked for the raw output and a diff three times and got a summary table instead.

Smaller things: it called Vossberg a car-rental company, which is nowhere in the repo. And one summary said all nine cars the rule missed had low km and high daily use. Four of them were just under 12,000 km and three had below-average daily use.

One thing was not Bob's fault but I found it on the way. verify.py passed "The average wear is correct" while the // was still in fleet_summary(), because it accepts 59.00 for 59.67. So there is now a test that checks the average to 0.01.

## What I checked before I accepted its work

I did not go by Bob saying it was done. After every step I had it run pytest and verify.py and paste the output. I also had a second assistant (Claude) run the tests and read the diffs directly in my folder, so I could compare that with what Bob claimed. That is how most of the things above came out.

- Wear bug: a car at 14,900 of 15,000 km now reports 99.3% and gets flagged. Before it was 0%.
- 80% rule: SERVICE_INTERVAL_KM is still 15000 and WARN_AT_PERCENT is still 80 in km_wachter.py, and settings.cfg has no changes at all in the diff.
- All 9 tests pass, from all three test files.
- The nightly report on fleet_sample.json prints the same numbers before and after the style clean-up (5 cars, 3 due, 109.2% average wear, 1 car with no reading, 163141.0 miles). So the modernizing did not change what the code does.
- 100 km is now 62.1 miles. Before it was 160.9.
- Before the five old helpers in fleet_utils.py were deleted I had it search that nothing calls them.

A car with no last-service reading is not flagged any more, but it is not hidden either. The report prints a "No reading" line with the count.

## What the data actually said

120 cars, 26 broke down. I compared the two groups column by column.

Three columns are different between the groups:

- km_since_service: 11,678 km for the cars that broke down, 7,261 km for the others
- avg_daily_km: 160 against 131
- load_factor: 0.60 against 0.51

Two are not. odometer_km is 53,448 against 53,302 and age_years is 5.9 in both groups. So total mileage and age, which look like the obvious answer, say nothing here. What matters is how far a car has gone since its last service and how hard it is used.

The combined score from the three columns is a bit better than km_since_service alone, but not a lot. Top 26: 16 breakdowns against 15. Top 32, which is how many cars the 80% rule flags: 17 for both. Top 40: 20 against 18. What it does well is pull up cars the rule misses, like VOS-1471 (rank 39 to 9) and VOS-1309 (rank 80 to 22). Both are under 12,000 km but driven hard with a high load.

This is all checked on the same 120 cars the score was built from, so on new cars it will probably be a little worse.
