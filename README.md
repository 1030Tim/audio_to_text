# 語音轉文字系統

一個使用 Python 建立的長時間錄音自動化處理系統。

本專案的主要目標，是將長時間的會議、課程或活動錄音，
透過 Speech-to-Text 與 Large Language Model，
自動轉換成較乾淨、容易閱讀的繁體中文逐字稿。


## Intro

由於我無法到學校參加系學會會議，

因此請同學代替我參加會議並錄下整場會議的內容。

收到錄音後，我原本需要自己重新聽完整段錄音，
一邊播放、一邊做筆記。
但當錄音長達三個多小時後，
我發現這種方式需要花費大量時間。
因此我開始思考：

> 能不能讓電腦自己把錄音轉成文字？

雖然目前已經有許多 Speech-to-Text 工具，
但長時間音檔在處理上仍可能遇到限制。
因此我決定自己建立一套完整的語音處理 Pipeline。

---

# Project Goal

本專案希望將：

長時間錄音
自動轉換成：
乾淨的繁體中文逐字稿

目前完整 Pipeline：

```text
Audio
  │
  ▼
讀取音檔
  │
  ▼
切割音檔
  │
  ▼
Faster-Whisper
  │
  ▼
Speech-to-Text
  │
  ▼
OpenCC
  │
  ▼
繁體中文
  │
  ▼
合併文字
  │
  ▼
文字切割
  │
  ▼
Gemini API
  │
  ▼
錯字與語意校正
  │
  ▼
Final Text
```

---

# Features

目前已完成：

* [x] 讀取 `.m4a` 音檔
* [x] 讀取 `.mp3` 音檔
* [x] 取得音檔基本資訊
* [x] 長時間音檔自動切割
* [x] 使用 Faster-Whisper 進行語音辨識
* [x] 使用 Whisper `large-v3`
* [x] 中文語音辨識
* [x] 使用 OpenCC 轉換繁體中文
* [x] 自動合併多個文字檔
* [x] 長文本自動切割
* [x] 使用 Gemini API 進行文字校稿
* [x] 保留原本語意的文字修正

---

# Tech Stack

| Technology       | Purpose        |
| ---------------- | -------------- |
| Python           | 主要開發語言         |
| Pydub            | 音訊讀取與切割        |
| FFmpeg           | 音訊格式處理         |
| Faster-Whisper   | Speech-to-Text |
| Whisper large-v3 | 語音辨識模型         |
| OpenCC           | 簡體中文轉繁體中文      |
| Gemini API       | 文字校稿與語意修正      |

---

# Project Structure

建議專案結構：

```text
├── main.py -> 主要功能函式
└── README.md
```

---

# Workflow

## 1. 取得音檔資訊

首先使用 Pydub 讀取音檔。

```python
from pydub import AudioSegment


def information(path):

    if path.endswith('.m4a'):

        audio = AudioSegment.from_file(
            path,
            format='m4a'
        )

    elif path.endswith('.mp3'):

        audio = AudioSegment.from_file(
            path,
            format='mp3'
        )

    else:

        raise ValueError("格式錯誤")

    print("檔案資訊")

    print(f"長度：{len(audio) / 1000:.2f} 秒")
    print(f"取樣率：{audio.frame_rate} Hz")
    print(f"聲道數：{audio.channels}")

    return audio
```

可以取得：

```text
音檔長度
取樣率
聲道數
```

---

# 2. 切割音檔

長時間音檔如果直接處理，
不容易管理，也會讓後續 Pipeline 變得比較難控制。

因此先將音檔切割成較短的片段。

目前設定：

```text
1 分鐘 / 一個音檔
```

例如一個三小時的錄音：

```text
test.m4a
   │
   ▼
Audio Split
   │
   ├── 1.m4a
   ├── 2.m4a
   ├── 3.m4a
   ├── ...
   └── 180.m4a
```

核心程式：

```python
def split_data(audio):

    output_dir = 'trans/split'

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    length = len(audio)

    chunk_length = 1 * 60 * 1000

    for i, start in enumerate(
        range(0, length, chunk_length),
        start=1
    ):

        end = min(
            start + chunk_length,
            length
        )

        chunk = audio[start:end]

        output_file = os.path.join(
            output_dir,
            f"{i}.m4a"
        )

        chunk.export(
            output_file,
            format='ipod'
        )

        print(f"完成：{output_file}")
```

---

# 3. Speech-to-Text

切割完成後，
使用 Faster-Whisper 對每個音檔進行語音辨識。

本專案使用：

```text
Whisper large-v3
```

並使用 CPU + INT8 進行推論。

```python
from faster_whisper import WhisperModel

model = WhisperModel(
    'large-v3',
    device='cpu',
    compute_type='int8',
    cpu_threads=8,
    num_workers=2
)
```

語音辨識：

```python
segments, info = model.transcribe(
    audio_file,
    language='zh',
    beam_size=5,
    vad_filter=True,
    condition_on_previous_text=False
)
```

其中：

```text
language='zh'
```

代表主要處理中文語音。

```text
vad_filter=True
```

則用於協助忽略沒有語音的區段。

---

# 4. 繁體中文轉換

語音辨識完成後，
使用 OpenCC 將辨識結果轉換成繁體中文。

```python
from opencc import OpenCC

cc = OpenCC('s2t')

text = cc.convert(text)
```

例如：

```text
今天我们要讨论这个问题
```

轉換為：

```text
今天我們要討論這個問題
```

---

# 5. 合併文字

每個音檔會產生一個文字檔：

```text
trans/text/

├── 1.txt
├── 2.txt
├── 3.txt
├── ...
```

接著按照檔案編號排序：

```text
1.txt
2.txt
3.txt
...
```

並合併成：

```text
trans/all_text.txt
```

這樣就可以重新建立完整的錄音逐字稿。

---

# 6. 長文本切割

完整逐字稿可能非常長。

如果直接將整份逐字稿送給 LLM，
可能受到 Context Window 或 Token 數量限制。

因此在送給 Gemini API 之前，
會先將文字切割成較小的區塊。

目前設定：

```text
500 行 / 一個檔案
```

例如：

```text
all_text.txt
     │
     ▼
Text Split
     │
     ├── split_1.txt
     ├── split_2.txt
     ├── split_3.txt
     └── ...
```

這個階段的概念是：

```text
Long Text
   │
   ├── Chunk 1
   ├── Chunk 2
   ├── Chunk 3
   └── ...
```

讓後續 LLM 可以分批處理。

---

# 7. Gemini API 校稿

Whisper 的主要任務是：

```text
Audio → Text
```

但是 Speech-to-Text 的結果可能會出現：

* 同音字
* 錯字
* 專有名詞辨識錯誤
* 斷句問題
* 不完整句子
* 標點符號問題

因此加入第二階段的 LLM Processing。

```text
Whisper
   │
   ▼
Raw Transcript
   │
   ▼
Gemini
   │
   ▼
Corrected Transcript
```

目前的 Prompt 原則：

```text
1. 修正明顯錯字
2. 修正同音字
3. 根據上下文判斷詞語
4. 修正明顯病句
5. 適度修正標點
6. 不改變原作者意思
7. 不過度潤飾
8. 不自行增加資訊
9. 不刪除重要資訊
10. 沒有問題的內容不要修改
11. 保留原本段落結構
12. 使用臺灣常用繁體中文
```

其中最重要的原則是：

> 不改變原作者原本想表達的意思。

因此 Gemini 在這個 Pipeline 中，
不是負責「重新寫文章」，

而是負責：

```text
Raw Transcript
      │
      ▼
理解上下文
      │
      ▼
修正辨識錯誤
      │
      ▼
保留原意
      │
      ▼
Clean Transcript
```

---

# Complete Pipeline

目前完整執行流程：

```python
if __name__ == '__main__':

    audio = information(
        'trans/test.m4a'
    )

    split_data(audio)

    audio2text()

    merge()

    split_text()

    modify()
```

也就是：

```text
1. Information
       ↓
2. Split Audio
       ↓
3. Speech-to-Text
       ↓
4. Traditional Chinese
       ↓
5. Merge Text
       ↓
6. Split Text
       ↓
7. Gemini Correction
```

---

# Example

假設輸入：

```text
trans/test.m4a
```

經過 Pipeline：

```text
test.m4a
    │
    ▼
trans/split/
    │
    ├── 1.m4a
    ├── 2.m4a
    ├── 3.m4a
    └── ...
    │
    ▼
trans/text/
    │
    ├── 1.txt
    ├── 2.txt
    ├── 3.txt
    └── ...
    │
    ▼
all_text.txt
    │
    ▼
text_split_output/
    │
    ├── split_1.txt
    ├── split_2.txt
    └── ...
    │
    ▼
Gemini API
    │
    ▼
final_1.txt
final_2.txt
final_3.txt
...
```

---

# Installation

Clone repository：

```bash
git clone <your-repository-url>

cd voice-to-text
```

建立 virtual environment：

```bash
python3 -m venv venv
```

啟動：

### macOS / Linux

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

安裝 dependencies：

```bash
pip install -r requirements.txt
```

---

# FFmpeg

本專案使用 Pydub 處理音訊，
因此需要安裝 FFmpeg。

macOS：

```bash
brew install ffmpeg
```

確認是否安裝成功：

```bash
ffmpeg -version
```

---

# API Key

Gemini API Key 不應直接寫入 Python 程式，
也不應該上傳到 GitHub。

建議使用：

```text
.env
```

或環境變數管理 API Key。

例如：

```text
GEMINI_API_KEY=your_api_key
```

並將：

```text
.env
```

加入 `.gitignore`。

---

# Requirements

目前主要 dependencies：

```text
pydub
faster-whisper
opencc
google-genai
```

可以使用：

```bash
pip freeze > requirements.txt
```

建立 requirements：

```text
requirements.txt
```

---

# Future Development

目前 Pipeline 已經可以完成：

```text
Audio
→
Speech-to-Text
→
Text Processing
→
LLM Correction
```

下一階段希望繼續改善：

```text
[ ] CLI 操作介面

[ ] 使用者可以自行指定輸入音檔

[ ] 自訂 Audio Chunk Length

[ ] 自訂 Text Chunk Size

[ ] Processing Progress Bar

[ ] Error Handling

[ ] Failed Chunk Retry

[ ] 自動偵測處理進度

[ ] 避免程式中斷後全部重新處理

[ ] Token-based Text Splitting

[ ] Speaker Diarization

[ ] Gemini API 自動摘要

[ ] Gemini API 自動整理會議重點

[ ] 自動產生會議紀錄

[ ] 完整 CLI Pipeline
```

---

# Project Concept

這個專案真正想解決的問題，
並不只是「把語音轉成文字」。

而是：

```text
聲音
 ↓
文字
 ↓
乾淨文字
 ↓
結構化資訊
```

也就是把原本需要人工花費數小時處理的資訊，

透過 Automation Pipeline 自動完成。

目前的核心架構可以簡化成：

```text
Audio Processing
       ↓
Speech Recognition
       ↓
Text Processing
       ↓
LLM Processing
       ↓
Information
```

語音辨識只是第一階段。

最終希望讓系統可以從：

> 「一個三小時的錄音」

直接變成：

> 「可以閱讀、搜尋、整理與理解的資訊」。



