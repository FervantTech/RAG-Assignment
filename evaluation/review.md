# Handbook evaluation review

Input: `data/Handbook.pdf`, the 2026 Full-Stack AI Engineer Bootcamp handbook.
The saved index contains 39 chunks. Sources use PDF-position page numbers.

## Recorded outcomes

- Twelve meaningful questions cover ten handbook topics plus two unsupported requests.
- All twelve initial HTTP requests returned 200; this alone does not imply answer correctness.
- Initial content check: 11/12 expected outcomes; the curriculum table question abstained.
- Latest curriculum API retest: correct topics and source, PDF page 6.
- Latest reviewed results: 12/12 expected outcomes, after retesting that question.
- Both unsupported questions returned exactly `answer unavailable` and a null source.
- Earlier unsuccessful attempts are preserved in `results.json`; they were not discarded.

## Question, answer, and source evidence

| # | Question | Answer | PDF source | Review |
|---|---|---|---|---|
| 1 | What is the course name? | The course name is the Full-Stack AI Engineer Bootcamp. | Page 1 | pass |
| 2 | What minimum internet download and upload speeds are recommended? | The recommended minimum internet speeds are 10 Mbps for download and 3 Mbps for upload. | Page 5 | pass |
| 3 | What topics are covered in weeks 11 to 15? | The topics covered in weeks 11 to 15 are ReactJS, Redux, Routing, API calls, Advanced React, Context, and Hooks. | Page 6 | pass after retest |
| 4 | What do green and yellow calendar tiles mean? | Green calendar tiles mean same day completion, demonstrating the ability to meet deadlines promptly. Yellow calendar tiles mean late completion, indicating tasks were completed after the designated day or more, serving as a learning opportunity for time management. | Page 9 | pass |
| 5 | When are live classes during the first 12 weeks? | During the first 12 weeks of the bootcamp, live classes are held from 6 pm to 8 pm on Wednesdays and from 9 am to 11 am on Mondays. | Page 11 | pass |
| 6 | Where are recorded lectures posted and assignments submitted? | Recorded lectures are posted on Google Classroom, and assignments are also shared and submitted on Google Classroom. | Page 13 | pass |
| 7 | What percentage of the final grade is the React and Node final project worth? | The React and Node final project is worth 35% of the final grade. | Page 14 | pass |
| 8 | What are the total bootcamp fees? | The total bootcamp fees are R 38,950. | Page 16 | pass |
| 9 | Which platform is the main communication channel after orientation? | After the orientation day and the official start of the boot camp, Discord serves as the primary platform for all communication. | Page 18 | pass |
| 10 | What are the tutor support hours on Tuesdays and Thursdays? | On Tuesdays, tutor support hours are from 2:00 PM to 4:00 PM and 6:00 PM to 8:00 PM. On Thursdays, they are from 10:00 AM to 12:00 PM and 6:00 PM to 8:00 PM. | Page 20 | pass |
| 11 | What is the campus Wi-Fi password? | answer unavailable | None | pass |
| 12 | What is the cafeteria lunch menu? | answer unavailable | None | pass |

## Limitations

Model output varied for the curriculum question. The cause of the earlier abstentions
has not been established. A successful retest is not a guarantee of future answers.
Citations are checked against retrieved quotes and pages, but this does not prove
every claim is semantically supported. The assistant reviewed answers against the
handbook text; the student should also inspect the evidence before handing in.

The handbook gives different overall durations on PDF pages 7 and 8; questions on
that topic should acknowledge the discrepancy. Fees and schedules are statements
in this handbook, not independently verified current policy.

This evaluation uses the student handbook.
