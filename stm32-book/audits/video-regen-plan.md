# Video regen plan (Bilibili-ready)

**Date (America/Adak):** 2026-11-04  
**HEAD at plan write:** see `git rev-parse HEAD` on `main`  
**Voice prefs:** `zh-CN-XiaoxiaoNeural`, rate **−5%**, pitch **−4Hz**; 1080p; covers/SRT/tags; narration anti-isomorphism; 逼真翔实生动 / 精美有趣.

## Inventory (ch00–28)

### Short films (`assets/video/chNN-*.mp4` via `tools/gen_narrated.py`)

| Range | Resolution / fps (sample) | Notes |
| --- | --- | --- |
| ch00–20 | **1920×1080** required by `check_assets` `hd_chapters` | ch03 already anti-iso + 1080p@8fps (gate). ch00/01/02/04/05 still end with shared **口诀 → … → 合上书，三问** template (except ch03). |
| ch21–28 | **960×540** @8fps (legacy) | Not yet in `hd_chapters`; upgrade later batch or extend HD allowlist intentionally. |

All 29 shorts have mp4+srt+png on disk. Duration contract: 120–240 s.

### Long lessons (`final-videos/chNN/chNN-bilibili-safe.mp4` via `tools/gen_long_lesson.py`)

| Range | storyboard.json | storyboard-rendered + media-report | bilibili-safe mp4 |
| --- | --- | --- | --- |
| ch00–15 | yes | yes | yes (1920×1080) |
| ch16–20 | yes | **missing** | yes (mp4 present; reports stale/absent) |
| ch21–25 | **no** | no | yes (legacy long mp4; no tracked storyboard) |
| ch26–28 | **no** | no | **missing** `final-videos/chNN/` |

Voice drift: some media-reports (e.g. ch05/ch15) show `Microsoft Huihui Desktop` SAPI fallback — **must regen with edge-tts Xiaoxiao** for contract voice.

`final-videos/` is gitignored; tracked evidence = `video/chNN/{storyboard.json,storyboard-rendered.json,media-report.json,*.srt,contact-sheet.jpg}` + short assets under `assets/video/`.

## Anti-isomorphism neighbor rule

Do not ship adjacent chapters with the same closing beat template (`口诀` / `合上书，三问`).  
ch03 is the reference diverse fingerprint (7 beats; no 口诀/合上书).  
Batch order diversifies neighbors before speak.

## Batch order

| Batch | Scope | Work |
| --- | --- | --- |
| **A (next execute)** | Shorts **ch00,01,02,04,05** (skip ch03) | Rewrite `tools/narration.py` endings for unique fingerprints vs neighbors; then `NARRATED_SCALE=2 NARRATED_FONT=C:\Windows\Fonts\msyh.ttc` `python tools/gen_narrated.py --speak NN` each; optional rate/pitch env once wired. |
| B | Longs **ch00–05** | Ensure storyboard role-order fingerprints differ; `gen_long_lesson.py --speak NN` with Xiaoxiao (no SAPI); refresh media-report. ch03 long already green. |
| C | Shorts **ch06–15** | Same anti-iso + 1080p speak. |
| D | Longs **ch06–15** | Regen; fix Huihui-voiced chapters. |
| E | Shorts **ch16–20** | Confirm 1080p; anti-iso; speak. |
| F | Longs **ch16–20** | Need rendered+report; `--speak` fills gaps. |
| G | ch21–28 | Author storyboards (long) + promote shorts to 1080p / extend `hd_chapters` only with intentional Spec note; create `final-videos/ch26–28`. |

## Commands (Windows PowerShell)

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:NARRATED_SCALE='2'
$env:NARRATED_FONT='C:\Windows\Fonts\msyh.ttc'
# preferred once code reads env (today RATE hardcoded -6%):
# $env:NARRATED_RATE='-5%'; $env:NARRATED_PITCH='-4Hz'
python tools/gen_narrated.py --check 00 01 02 04 05
python tools/gen_narrated.py --speak 00
# … per chapter …
Remove-Item Env:NARRATED_SCALE -ErrorAction SilentlyContinue  # check_assets expects default scale for poster math unless FONT skip
python tools/check_assets.py
python tools/gen_long_lesson.py --check 00
python tools/gen_long_lesson.py --speak 00
python tools/gen_long_lesson.py --report 00
```

## QA checklist (per chapter)

- [ ] Short: 1920×1080 H.264 + AAC; duration 120–240 s; SRT cue text == narration `say`; voice present.
- [ ] Short fingerprint ≠ immediate neighbors (heads + closing beat).
- [ ] Long (when in batch): media-report checks all true; 1080p 30fps; XiaoxiaoNeural; LUFS/peak; contact-sheet; storyboard SHA recorded.
- [ ] `pytest` / `check_assets` / `slop_lint` / `audit_book` / `build_html --check` zh+en green; **no assertion weakening**.
- [ ] Covers/SRT/tags present or regenerated via existing `gen_platform_covers` / chapter md as needed.

## Blockers / open

1. **RATE/PITCH:** `gen_narrated.py` hardcodes `RATE="-6%"` and no pitch — wire env defaults to −5% / −4Hz before Batch A speak (small tools change).
2. **ch21–28 long storyboards** missing — authoring cost before G.
3. **ch26–28** no `final-videos` dirs yet.
4. **SAPI fallback chapters** must not count as final Xiaoxiao deliverables.
5. Full 29×2 regen is multi-hour; stay batched; PDF rebuild already done this session (zh+en).

## Status
## Status

- [x] 全书反同构指纹普查（**2026-11-05**，收尾轮）：29 章相邻章最后两拍 0 重复；「合上书，三问」模板清零；口诀保留于 00/02/21/23，互不相邻。
- [x] 收尾门（**2026-11-05**）：pytest 182 passed；check_assets 1962/1962（hd_chapters=29）；slop_lint 干净；audit_book zh/en 锚点各 439、低于目标 0；PDF zh/en 重建（含 Batch A–G 全部旁白稿源）。


- [x] Inventory
- [x] This plan file
- [x] Batch A execute（**2026-11-05**）：ch00/01/02/04/05 旁白结尾反同构改写（五章指纹互不相同、≠ch03/ch06），NARRATED_RATE/NARRATED_PITCH 环境变量接线（Blocker 1 关闭），1080p 重配音 ch00 139.3s / ch01 146.9s / ch02 155.5s / ch04 157.2s / ch05 161.0s，文档旁白稿 `--patch-docs` 同步；QA：ffprobe 逐条核验、check_assets 1962/1962、pytest 182 passed。
- [x] ch03 pilot 端到端复跑（**2026-11-05**）：短片 `--speak 03` 121.4s/1080p/7 条字幕（TTS 断连重试生效）；长课 `--report 03` 十项全 True、SHA 在 media-report。
- [x] Batch B execute（**2026-11-05**）：ch01/02/04/05 长课 Huihui→XiaoxiaoNeural 重配音完成
- [x] Batch C execute（**2026-11-05**）：ch06–15 十章短片结尾拍反同构改写（每章取自本章事实），1080p 重配音 149.0–170.8 s 全部在合同内；zh+en 文档旁白稿同步；QA ffprobe + check_assets 1962/1962 + pytest 182 passed（commit `ac7bdca`）。
- [x] Batch D execute（**2026-11-05**）：ch06–15 长课 Huihui→XiaoxiaoNeural 重配音，media-report 十项全 True（commit `90b22d6`）。ch00–15 十六章长课全部 Xiaoxiao 达标。
- [x] Batch E execute（**2026-11-05**）：ch16–20 五章短片结尾拍反同构改写 + 1080p 重配音 146.9–162.8 s（commit `a6be916`）。
- [x] Batch F execute（**2026-11-05**）：ch16–20 长课整链重配音完成——rendered storyboard + media-report 十项全 True + XiaoxiaoNeural + 联系表；`video/ch16–20/` 证据链补齐。ch00–20 十六章长课 + 二十一章短片（00–20）全部为 Xiaoxiao 可复现交付。
- [x] Batch G execute（**2026-11-05**）：ch21–28 八份长课 storyboard 自编完成（每章 28 场景五角色，逐条取材本章正文，全部过 --check）+ Xiaoxiao 整链重配音（media-report 十项全 True）；短片 ch21–28 结尾拍反同构改写 + NARRATED_SCALE=2 重配音为 1080p；check_assets `hd_chapters` 扩围至 29 章（Spec 说明已写入 check_assets 注释与本行）；`final-videos/ch26–28` 已由长课链建立。至此 29 短片 + 29 长课全部由当前源可再生。
