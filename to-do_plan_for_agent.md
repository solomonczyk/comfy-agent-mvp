| День | Слой / задача                      | Что сделать                                                                                                                                          | Definition of Done                                                                                                  | Что вернуть                                                                                |
| ---- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| 1    | **KT-1 finish**                    | Исправить `filename_prefix`, добавить его в parity, сделать **один чистый RealVis canonical re-run** без загрязнённой очереди                        | Есть completed run; `requested = mutated = submitted = executed`; есть final image, `metadata_path`, `summary_path` | список файлов, `prompt_id`, parity fragment, image path, metadata path, summary path       |
| 2    | **KT-2 start**                     | Создать `app/tools/`, `tool_types.py`, `tool_trace.py`, thin wrappers: `detect_task`, `select_workflow`, `validate_required_inputs`, `load_workflow` | Trace JSONL создаётся; первые tool events пишутся                                                                   | список файлов, пример JSONL trace, список первых tools                                     |
| 3    | **KT-2 continue**                  | Добавить `validate_graph_contract`, `mutate_workflow`, `submit_to_comfy`, `watch_progress`, `fetch_outputs`, `persist_run`                           | Portrait и edit path дают полный `tool_chain`                                                                       | portrait trace, edit trace, `trace_path`, `tool_chain`                                     |
| 4    | **KT-2 stabilize**                 | Убрать регрессии, проверить `tool_trace=None`, прогнать тесты KT-2                                                                                   | KT-2 branch соответствует критериям; KT-1 не сломан                                                                 | PASS/FAIL по KT-2 criteria, тесты, no-regression proof                                     |
| 5    | **KT-4 start**                     | Ввести `batch_run`, pack spec, sequential/controlled execution на 5–10 jobs                                                                          | Первый batch запускается headless                                                                                   | batch command, pack spec, manifest, job statuses                                           |
| 6    | **KT-4 finish**                    | Сгруппировать outputs по run/job, сделать comparison summary                                                                                         | Один completed batch pack с output tree и summary                                                                   | completed batch folder, manifest, comparison summary                                       |
| 7    | **KT-5 start**                     | Ввести минимальную структуру папок: `inputs/`, `references/`, `outputs/`, `batches/`, `manifests/`, `traces/`, `videos/`                             | Один run и один batch складываются в структурированное дерево                                                       | folder tree, naming rules, один run + batch пример                                         |
| 8    | **KT-6 start**                     | Сделать `extract_frames` для локального видео, сохранить manifest                                                                                    | Видео раскладывается на кадры headless                                                                              | input video path, extracted frames folder, manifest                                        |
| 9    | **KT-6 continue**                  | Прогнать часть кадров через image/edit pipeline, сохранить `edited_frames`                                                                           | Несколько кадров реально проходят через ComfyUI path                                                                | input frames, edited frames, trace                                                         |
| 10   | **KT-6 finish**                    | Собрать кадры обратно в видео через FFmpeg, сохранить export manifest                                                                                | Есть `video out`                                                                                                    | output video path, export manifest                                                         |
| 11   | **KT-8 partial (video QC min)**    | Минимальный video QC: black/blank frames, broken export, missing frames, severe flicker heuristic, bad crop heuristic                                | Есть первый `video_qc_report`                                                                                       | qc report, один accept/retry/reject пример                                                 |
| 12   | **End-to-end scenario**            | Прогнать один полный сценарий: input → headless run → trace → outputs → manifest → video path если нужен                                             | Система ощущается как один инструмент, а не набор кусков                                                            | одна команда, один полный сценарий, все artifact paths                                     |
| 13   | **Critical seam fixes only**       | Чинить только то, что реально мешает использовать: пути, naming, команды, лишняя ручная возня                                                        | Комбайн usable для ежедневной работы                                                                                | список критичных fixes, что ещё осталось ручным                                            |
| 14   | **Control build / acceptance day** | Прогнать 4 сценария: portrait, edit, batch, video in→out                                                                                             | Комбайн v1 usable                                                                                                   | 4 команды, 4 completed scenarios, output tree, trace files, manifests, список хвостов v1.1 |
Жёсткие правила на все 14 дней
Что делать
двигаться только по слоям, которые открывают новый класс возможностей;
держать medium refactor only;
принимать ugly-but-useful;
возвращаться с артефактами, а не с обещаниями.
Что не делать
checkpoint comparison
Juggernaut / DreamShaper exploration
advanced QC hardening
heavy refactor монолита
новый UI
“ещё один proof ради proof”
сложный video intelligence / auto montage
Главные контрольные точки
KT-1

RealVis canonical run green

KT-2

Visible internal tool layer

KT-4

Headless batch pack

KT-5

Structured local asset tree

KT-6

Video in → frames → processed video out

Минимальный набор команд, который должен появиться к концу плана
Portrait
python -m app.agent_run --prompt "realistic female portrait" --mode portrait --canonical-recipe
Edit
python -m app.agent_run --prompt "improve realism and details" --mode edit --input-image <path>
Batch
python -m app.batch_run --spec <batch_spec.json>
Video
python -m app.video_run --input-video <video_path>
Что должен возвращать агент каждый день

Каждый день ответ должен быть в одном формате:

Что разблокировано
Список изменённых файлов
Команда запуска
Артефакты
PASS/FAIL
Что осталось ручным


windsurfe

FAST-TRACK 14-DAY EXECUTION PLAN

Goal:
Finish a usable personal local ComfyUI combine as fast as possible.

Rules:
- only work on layers that unlock a new capability class
- medium refactor only
- ugly but useful is acceptable
- return proof artifacts, not narrative
- freeze until further notice:
  checkpoint comparison, Juggernaut/DreamShaper testing, advanced QC hardening, heavy monolith refactor, UI work, advanced montage intelligence

Day 1:
Close KT-1 with filename_prefix fix + parity + one clean RealVis canonical re-run

Day 2-4:
KT-2 Internal Tool Layer Consolidation v1
Required tools:
detect_task
select_workflow
validate_required_inputs
validate_graph_contract
load_workflow
mutate_workflow
submit_to_comfy
watch_progress
fetch_outputs
persist_run

Day 5-6:
KT-4 Batch Pack Orchestration v1
One batch pack, 5-10 jobs, manifest, structured outputs

Day 7:
KT-5 minimal asset pipeline
Structured folders and naming rules

Day 8-10:
KT-6 Video Operations Core v1
Input video -> extract frames -> process selected frames -> reassemble export

Day 11:
Minimal video QC

Day 12:
One end-to-end combined scenario

Day 13:
Critical seam fixes only

Day 14:
Control build / acceptance day:
portrait + edit + batch + video

Daily return format:
- capability unlocked
- changed files
- run command
- artifact paths
- PASS/FAIL
- what is still manual