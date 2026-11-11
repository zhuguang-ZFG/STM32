# v2 云扬语速探针与初始发音表

Task 7 交付，2026-10-22。用途：Task 11（S5 端到端样板）选 `rate`、把 `ttsLexicon` 落进
`episode.json`。本文件只给实测值与候选规则，**不替用户选 rate**——最终值由用户抽听三份样本 + 字/秒定。

## 环境与测法

- Python 3.13.14；`edge_tts` 7.3.1（`python -c "import edge_tts; print(edge_tts.__version__)"`）。
- 仓库只有 `ffmpeg-static` 的 ffmpeg，没有 ffprobe；时长用解码到 null、读最后一行 `time=`，
  与 `video/src/audio/assemble.py` 的 `probe_duration()` 同法（对无 Xing 头的 mp3 也可信）。
- 探针脚本 `.temp/v2-voice-probe.mjs`、试听样例 `.temp/v2-voice-demo.mjs`（`.temp/` 已 gitignore）。

## 语速探针（同一句，三档）

文本（54 字符含空格 / 50 去空白，其中汉字 29）：

```text
SysTick 每毫秒跳一次，先把重装值算准，再开中断。GPIOF 的 BSRR 写一位就翻转，不用读改写。
```

| rate | 文件 | 实测时长 | 字/秒（54 字符） | 字/秒（50 去空白） | 体积 |
|---|---|---|---|---|---|
| `+0%` | `.temp/voice/rate-p0.mp3` | 9.60 s | 5.63 | 5.21 | 57744 B |
| `+2%` | `.temp/voice/rate-p2.mp3` | 9.43 s | 5.73 | 5.30 | 56736 B |
| `+4%` | `.temp/voice/rate-p4.mp3` | 9.24 s | 5.84 | 5.41 | 55584 B |

`+0% → +4%` 在这句上只省 0.36 s（3.8%）；三档差距要靠耳朵定，数字只作旁证。
三份文件可直接抽听，路径见上表。

实际执行（每档一条，`--text` 为上面整句）：

```bash
python -m edge_tts --voice zh-CN-YunyangNeural --rate=+0% --text "SysTick 每毫秒跳一次，先把重装值算准，再开中断。GPIOF 的 BSRR 写一位就翻转，不用读改写。" --write-media .temp/voice/rate-p0.mp3
node_modules/ffmpeg-static/ffmpeg.exe -hide_banner -i .temp/voice/rate-p0.mp3 -map a:0 -f null -
# +2% / +4% 同法，输出到 rate-p2.mp3 / rate-p4.mp3
```

批量脚本入口：`node .temp/v2-voice-probe.mjs`（生成 + 量时长 + 打印上表）。

## 发音表试听样例

`node .temp/v2-voice-demo.mjs`，云扬 `+2%`，产物 `.temp/voice/lexicon-demo-p2.mp3`（8.90 s）：

```text
原文 : 先看地址 0x40021418，再读 GPIOF 的 BSRR，SysTick 每毫秒跳一次。
TTS  : 先看地址 零 x 四零零二一四一八，再读 G P I O F 的 B S R R，Sys tick 每毫秒跳一次。
```

与 `rate-p2.mp3` 对照听，可判断"字母拆读 + 地址逐位读"是否达到想要的效果。

## 提议的初始 `ttsLexicon`

```json
{
  "0x": "零 x ",
  "offsetof": "offset of",
  "BSRR": "B S R R",
  "PendSV": "Pend S V",
  "SysTick": "Sys tick",
  "GPIOF": "G P I O F",
  "GPIO": "G P I O",
  "MHz": "兆赫",
  " ms": " 毫秒",
  " us": " 微秒",
  "LR": "L R",
  "PC": "P C ",
  "SP": "S P"
}
```

说明：

- `0x` 只是兜底（读"零 x"）；地址要逐位读，必须按下一节规则为每个字面量再生成一条长键。
- **键是字面子串**，`applyLexicon` 只做 `split/join`，不认词边界；标识符拆到哪，由作者按正文实际字符串加键。
  下面箭头均为上表 + `applyLexicon` 的实算输出。
- `GPIOF` 命中 5 字符长键 → `G P I O F`；`GPIOA` 只命中 `GPIO` → `G P I OA`。两条键都保留：
  删掉 `GPIOF` 后 `GPIO` 会把 `GPIOF` 读成 `G P I OF`；正文若真有 `GPIOA/B/C`，请补整词键。
- `SP` 只在字面 `SP` 处替换：`SPI` → `S PI`、`PSP` → `PS P`、`MSP` → `MS P`；没有一个能当可靠的逐字母读法。
  要 `S P I` / `P S P` / `M S P`，给整词键（`"SPI": "S P I"`、`"PSP": "P S P"`、`"MSP": "M S P"`），不要指望一条 `SP` 通吃。
- `PC` 的值末尾有一个**有意保留的空格**：`PC13` → `P C 13`、`PC0` → `P C 0`，否则是 `P C13`，数字容易黏成"P C 十三"。
- `MHz` 用中文单位"兆赫"，避免 TTS 把 `MHz` 念成一个怪词；`168MHz` → `168兆赫`。
- 键区分大小写；上表只覆盖内容里实际出现的大小写形式，Task 11 落地前按正文逐个字符串核对输出。

### 为什么 ms / us 用带前导空格的键

`applyLexicon` 是纯 `split/join`，没有词边界。裸键 `"us"` 会把现稿旁白里的 `push`（5 处）
改成 `p微秒h`；裸键 `"ms"` 会打中 `platforms` / `params` 这类词（全文件分别 19 / 5 处，
只是当前旁白恰好没用到）。因此初始表用 `" ms"` / `" us"`，并约定旁白数字与单位之间留空格。
代价是紧凑写法不覆盖（现 S5 旁白有 `5us`）：Task 11 要么写成 `5 us`，要么按下一节为
每个紧凑字面量补一条长键（`"5us": "5 微秒"`）。

## 0x 通用规则（逐位读，不是某一条地址）

对旁白/ttsText 里出现的**每一个** `0x[0-9A-Fa-f]+` 字面量，各生成一条以该字面量为键的条目；
数字用中文数字连写，A–F 用大写字母、两侧加空格。长键优先**只在该字面量自己也有键时**成立：
`0xC` 有键时不会先被 `0x` 拆掉；漏了 `0xC0` 的键，`0xC` 仍会把它改成 `零 x C0`（见下）。

```js
const CN = '零一二三四五六七八九'
// 输入字面量，返回该键的发音值
function hexValue(lit) {
  const body = lit.slice(2)
    .replace(/[0-9a-f]/gi, (c) => (/\d/.test(c) ? CN[Number(c)] : ` ${c.toUpperCase()} `))
    .replace(/\s+/g, ' ')
    .trim()
  return `零 x ${body}`
}

// 落地到某集时：枚举该集出现的所有字面量（大小写按原文）
const texts = /* 该集所有 narration + ttsText */ ''
const lex = {}
for (const lit of new Set(texts.match(/0x[0-9a-fA-F]+/g) ?? [])) lex[lit] = hexValue(lit)
```

输出示例（规则验证，非只针对某一条；把下面各字面量的键连同 `"0x"` 交给 `applyLexicon` 实算）：

```text
0x40021418 => 零 x 四零零二一四一八
0xE000E010 => 零 x E 零零零 E 零一零
0xFFFFFC18 => 零 x F F F F F C 一八
0xC        => 零 x C
0x000      => 零 x 零零零
0xF0       => 零 x F 零
0xDEADBEEF => 零 x D E A D B E E F
```

要点：生成必须覆盖**全部**字面量，不能只给一条示例。若只放 `"0xC"` 而正文还有 `"0xC0"`，
长键优先也救不了——`0xC0` 没有自己的键，会先被 `0xC` 改成 `零 x C0`。

### 紧凑单位同样按字面量补键

```js
for (const m of texts.matchAll(/\d+(?:ms|us)\b/g)) {
  lex[m[0]] = m[0].replace(/ms$/, ' 毫秒').replace(/us$/, ' 微秒')
}
// "5us" => "5 微秒"；"100ms" => "100 毫秒"
```

键长 ≥2，`5us` / `100ms` 都合法；长键优先于 `" ms"` / `" us"`。

## 已知边界

- **词表是纯字符串替换**：ttsText 里若仍残留键（作者漏展开），合成时还会被替换，不会静默放过
  （`video/tests/tts-lexicon.test.mjs` 有断言）。
- `SysTick_Handler`、`PendSV_Handler` 这类带下划线的全名，`SysTick` / `PendSV` 只展开前半段，
  `_Handler` 原样留给 TTS。需要时可再加整名长键。
- `plausible()` 现在按 ttsText 的字数算语速。字母拆读加的空格会抬高"字/秒"（如 `GPIOF` 5 → 9 字符），
  本句 5.2–5.8 字/秒，离 `MAX_SPEED = 9.5` 还有余量；缩写极密的句子仍可能逼近阈值，留意重试日志。
- v1 的缓存键不变（无词表时 `spoken_text == narration`）；`audioStamp` 因 scenes 新增 `ttsText`
  会触发一次重跑，但句子全部命中缓存，音频/时间轴字节不变。
