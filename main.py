from pydub import AudioSegment
import os

# 取得音樂
def imformation(path):
    if path.endswith('.m4a'):
        audio = AudioSegment.from_file(path, format='m4a')
    elif path.endswith('.mp3'):
        audio = AudioSegment.from_file(path, format='mp4')
    else:
        print("格式錯誤")

    print("檔案資訊")
    print(f"長度{len(audio)/1000:.2f}秒")
    print(f"取量率{audio.frame_rate} HZ")
    print(f"聲道數{audio.channels}")

    return audio

#切割音樂
def split_data(audio):

    output_dir = 'trans/split'
    os.makedirs("trans/split", exist_ok=True)

    lenght = len(audio)
    chunk_lenght = 1*60*1000
    

    for i, start in enumerate(range(0, lenght, chunk_lenght), start=1):
        end = min(start + chunk_lenght, len(audio))

        chunk = audio[start:end]
        output_file = os.path.join(
        output_dir,
        f"{i}.m4a"
        )
        chunk.export(output_file, format = 'ipod')
        
        print(f"完成{output_file}")
    print("全部完成")


# 語音轉文字模型
def audio2text():

    from faster_whisper import WhisperModel
    from opencc import OpenCC

    cc = OpenCC('s2t')

    audio_path = '/Users/juhn/Desktop/agent/trans/split'
    files = list(os.listdir(audio_path))

    files = sorted(
    [
        file
        for file in os.listdir(audio_path)
        if file.endswith('.m4a')
    ],
    key=lambda x: int(os.path.splitext(x)[0])
    )

    # 設定模型
    model = WhisperModel(
        'large-v3',
        device='cpu',
        compute_type='int8',
        cpu_threads=8,
        num_workers=2
    )

    #輸出路徑
    output_dir = 'trans/text'
    os.makedirs(output_dir, exist_ok=True)


    for i, file in enumerate(files, start = 1):
        print(f'目前正在處理{file}')
        audio_file = os.path.join(audio_path, file)
        print(file)
        # 設定語言
        segments, info = model.transcribe(
        str(audio_file),
        
        language='zh',
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False)

        segments = list(segments)
        print(segments)
        print(f'語言：{info.language}')
        print(f'語言機率：{info.language_probability:.2f}')
        print(f'音檔長度：{info.duration:.2f} 秒')



        file_name = os.path.splitext(file)[0]
        output_file = os.path.join(
            output_dir,
            f'{file_name}.txt')

        with open(output_file, 'w', encoding='utf-8') as f:
            for segment in segments:
                text = segment.text.strip()
                text = cc.convert(text)
                if text:
                    f.write(text+'\n')
        print(f'完成{output_file}')

# 合併文字檔
def marge():
    text_path = '/Users/juhn/Desktop/agent/trans/text'
    output_file = '/Users/juhn/Desktop/agent/trans/all_text.txt'
    files = sorted(
        [
            file
            for file in os.listdir(text_path)
            if file.endswith('.txt')
        ],
        key=lambda x: int(os.path.splitext(x)[0])
        )
    with open(output_file, 'w', encoding='utf-8') as outfile:

        for file in files:

            file_path = os.path.join(text_path, file)

            print(f'正在合併：{file}')

            with open(file_path, 'r', encoding='utf-8') as infile:
                text = infile.read()

            outfile.write(text)

            # 每個檔案中間空一行
            outfile.write('\n\n')

            print(f'合併完成：{output_file}')

# 切割完整文本
def split_text():
    text_split_dir = '/Users/juhn/Desktop/agent/trans/text_split_output'
    os.makedirs(text_split_dir, exist_ok=True)

    with open('/Users/juhn/Desktop/agent/trans/all_text.txt', 'r', encoding='utf-8') as f:
        text = [
            line.strip()
            for line in f
                if line.strip()
            ]

    if len(text) > 500:
        print(f'共有{len(text)}開始分割')
        chunk_size = 500
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            split_number = i//chunk_size+1

            output_file = os.path.join(
                text_split_dir,
                f'split_{split_number}.txt'
            )

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(chunk))
                f.write('\n')
            print(f'完成{output_file}')
    else:
        print(f'只有{len(text)}不用分割')
        output_file = os.path.join(
            text_split_dir,
            'split_1.txt'
        )
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(text))
            f.write('\n')


def modify():
    #串接api
    global api_key
    with open('/Users/juhn/Desktop/agent/.env/api_key.txt', 'r', encoding='utf-8') as f:
        api_key = f.read()
        print(api_key)
        f.close()
    from google import genai
    
    client = genai.Client(
            api_key = api_key.strip()
    )
    # 路徑
    text_path = 'trans/text_split_output'
    output_path = 'trans/text_split_output'

    # 排序檔案
    files = sorted([
        file
        for file in os.listdir(text_path)
        if file.startswith('split_') and file.endswith('.txt')
    ],
    key = lambda x:int(
        os.path.splitext(x)[0].split('_')[1]
    ) )
    count = 1
    for file in files:
        global text
        with open(text_path+'/'+file, 'r', encoding='utf-8') as f:
            text = f.read()
        print(text)

        
        prompt = f"""
        以下是語音轉文字的辨識結果：
        {text}
        請你先理解整段文字的上下文、語意與情境，再進行校稿。
        請依照以下規則處理：
        1. 修正明顯的錯字、同音字或語音辨識造成的文字錯誤。
        2. 根據上下文判斷詞語是否合理，不要只按照單一句子判斷。
        3. 修正明顯不通順、語意不完整或明顯的病句。
        4. 如果標點符號或斷句明顯錯誤，可以適度修正。
        5. 不要任意改變原作者的意思。
        6. 「不改變原作者原本想表達的意思」是最高原則。
        7. 不要過度潤飾，不要把口語內容改成正式文章。
        8. 不要自行增加原文沒有提到的資訊。
        9. 不要刪除原文的重要資訊。
        10. 如果原文沒有明顯問題，就不要修改。
        11. 保留原本的段落結構與內容順序。
        12. 使用臺灣常用的繁體中文。

        最重要的原則：
        即使你認為某種說法更漂亮、更正式，只要修改後可能改變原作者的意思，就不要修改。

        輸出規則：
        - 只輸出修正後的完整文章。
        - 不要輸出分析過程。
        - 不要解釋修改原因。
        - 不要加入「修正後」、「修改結果」等標題。
        - 不要使用 Markdown。
        - 保留原本的段落與換行。
        """

        response = client.models.generate_content(
            model = 'gemini-3.5-flash',
            contents = prompt
        )


        output_file = os.path.join(
            output_path,
            f'final_{count}.txt'
        )
        with open(f'{output_path}/final_{count}.txt', 'w', encoding='utf-8') as f:
            f.write(str(response.text))
            f.write('\n')
        count+=1



if __name__ == '__main__':
    audio = imformation('/Users/juhn/Desktop/agent/trans/test.m4a')
    split_data(audio)
    audio2text()
    marge()
    split_text()
    modify()