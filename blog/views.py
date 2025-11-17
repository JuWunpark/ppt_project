import pickle
from django.shortcuts import render, redirect
from googleapiclient.errors import HttpError
from .forms import SignUpForm, UserUpdateForm, ProfileUpdateForm
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import os, re, openai, json, io
import random
import logging
from django.http import HttpResponse
from .models import UserHistory
from django.conf import settings
import openai
import re
from collections import OrderedDict



# OpenAI 설정
SLIDE_TITLE_TEXT = ' '
filename = ' '
ppt_link = ' '
client = openai.Client(
    api_key=settings.OPENAI_API_KEY)  # API Key

# API 권한 범위 설정
SCOPES = ['https://www.googleapis.com/auth/presentations.readonly']
presentation_id=''


def signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "회원가입이 완료되었습니다!")
            return redirect('sign_in')
        else:
            messages.error(request, "회원가입에 실패했습니다. 입력 정보를 확인해주세요.")

    else:
        form = SignUpForm()

    return render(request, 'blog/signup.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')  # 이미 로그인한 사용자는 홈으로 리디렉트

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "로그인에 성공했습니다.")

            # 로그인 후 이동할 URL 결정
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)  # 리디렉트 수행
        else:
            print(f"로그인 실패: {form.errors}")  # ❌ 로그인 실패 이유 출력 (디버깅)
            messages.error(request, "아이디 또는 비밀번호가 올바르지 않습니다.")

    else:
        form = AuthenticationForm()

    return render(request, 'blog/login.html', {'form': form})
def user_logout(request):
    logout(request)
    messages.success(request, "로그아웃되었습니다.")
    return redirect('home')

### 🔹 회원 정보 수정 (Update Profile)
@login_required #데코레이터로 로그인한 사용자만 수정 가능
def user_update(request):
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')  # 회원정보 수정 후 이동할 페이지
    else:
        form = UserUpdateForm(instance=request.user) #현재 로그인한 사용자의 정보 가져오기
    return render(request, 'blog/user_update.html', {'form': form})

@login_required
def profile_view(request):
    user_id=request.user.id
    user_histories = UserHistory.objects.filter(user_id=user_id).order_by('-create_date')

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)

        if form.is_valid():
            # user_id = form.cleaned_data['id']
            # print(user_id)
            form.save()
            messages.success(request, "프로필이 성공적으로 업데이트되었습니다.")
            # return redirect('profile')  # 새로고침하면서 반영됨
            return render(request, 'blog/profile.html', {'form': form, 'user_histories': user_histories})  # 👈 데이터 유지
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'blog/profile.html', {'form': form, 'user_histories': user_histories})


def delete_user_history(request):
    if request.method == "POST":
        selected_ids = request.POST.getlist('presentation_id')  # 선택된 체크박스 값 가져오기
        # selected_ids=int(selected_ids)
        UserHistory.objects.filter(id__in=selected_ids, user=request.user).delete()  # 삭제 실행
        messages.success(request, "선택한 항목이 삭제되었습니다.")

    return redirect('profile')


## 🔹 비밀번호 변경 (Password Change)
@login_required
def password_change(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # 비밀번호 변경 후 로그인 유지
            return redirect('home')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'blog/password_change.html', {'form': form})

def home(request):
    return render(request, 'home_login.html')
@login_required(login_url='/login/')
def Sign_in_home(request):
    # if request.user.is_authenticated:
    #     return redirect('sign_in')  # ✅ 로그인한 경우 홈으로 이동
    return render(request, 'home_login.html')

@login_required(login_url='/login/')
def prompt(request):
    # form = ProfileUpdateForm(request.POST, instance=request.user)
    user_id = request.user.id


    global SLIDE_TITLE_TEXT
    global filename
    global ppt_link
    if request.method == "POST":
        presentation_id = request.POST.get("presentation_id")
        print(presentation_id, "입력받은 ID값")
     
        SLIDE_TITLE_TEXT = request.POST.get("user-input", "").strip()
     
        input_string = re.sub(r"[^\w\s.\-\(\)]", "", SLIDE_TITLE_TEXT).replace("\n", "")

        filename_prompt = (f"Generate a short, descriptive filename based on the following input: \"{input_string}\". "
                           f"Answer just with the short filename, no explanation.")

        filename_response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",  # 여기에 맞춰 모델 설정
            messages=[{"role": "system", "content": filename_prompt}],
            temperature=0.5,
            max_tokens=30,
        )

        filename = filename_response.choices[0].message.content.strip().replace(" ", "_")
        # gpt가 변경한 코드 
        # dir_name = filename
        # os.makedirs(dir_name, exist_ok=True)  # 이미 있어도 에러 안 냄
        # SLIDE_TITLE_TEXT = dir_name

        raw_title = filename_response.choices[0].message.content.strip()

        # 공백 → '_' 로 바꾸고, 기존에 이상한 확장자가 붙어 있으면 제거
        base_name = raw_title.replace(" ", "_")
        base_name = os.path.splitext(base_name)[0]      # '...발표1.docx' -> '...발표1'

        # 1) 폴더 이름(확장자 없음) : txt 파일들이 들어갈 디렉터리
        dir_name = base_name

        # 2) PPT 제목(확장자 .ppt) : 구글 슬라이드 파일명으로 쓸 문자열
        ppt_title = base_name + ".ppt"

        # 전역 변수에 반영
        filename = dir_name               # 나머지 코드에서 파일/폴더 경로용으로 쓰는 이름
        os.makedirs(dir_name, exist_ok=True)
        SLIDE_TITLE_TEXT = ppt_title      # create_slides() 에서 슬라이드 이름으로 사용

        ppt_text = create_ppt_text(filename)

        split_slides(ppt_text, index=0)

        ppt_detail_text = create_ppt_detail_text()
        split_slides(ppt_detail_text, index=2)
        ppt_link=create_slides(presentation_id, filename)
        print("👉 ppt_link =", repr(ppt_link))
        if not ppt_link:
    # 일단은 임시로 그냥 에러 텍스트 찍고 멈추자
            return HttpResponse("슬라이드 링크 생성에 실패했습니다. 터미널 로그를 확인하세요.")


        UserHistory.objects.create(user_id=user_id, ppt_url=ppt_link, ppt_title=filename)

        

        return redirect('result')
    else:
        return render(request, 'blog/prompt.html')

# -- 프롬프트 --#######################################################################################

def create_ppt_text(topic):
    
    prompt = f"""
        Write a PowerPoint presentation about "{topic}". Follow these rules strictly:

        2. **Slide 1**: Title slide (only title & subtitle).
        3. **Slide 2**: Table of Contents (list all slide topics, no images).
        7. Result must only be in Korean and should follow the specified structure.

        Use the following format strictly:
        #Title: [PPT 제목]

        #Slide: 1
        #Header: [PPT 제목]
        #Content: [PPT 제목에 대한 부가 설명]

        #Slide: 2
        #Header: 목차
        #Content: 
        1. [목차 제목 1]
        ...
        """
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=4096,
    )
    return response.choices[0].message.content.strip()

def create_ppt_detail_text():
    global SLIDE_TITLE_TEXT
    """GPT를 활용하여 PPT 내용을 자동 생성 (슬라이드 개수 & 구조 강제)"""
    try:
        file_path = f"{SLIDE_TITLE_TEXT}/0_목차.txt"
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()  # 처음 1200자만 읽기
    except FileNotFoundError:
        file_path = f"{SLIDE_TITLE_TEXT}/1_목차.txt"
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()  # 처음 1200자만 읽기

    prompt = f"""
    Write an a about "{content}". Follow these rules strictly:


   The topics listed in the table of contents are the themes 
   I want to include in my PowerPoint presentation. 
   Please provide detailed content for each topic. 
   The total length should be between 2000 and 3000 characters. 
   Make sure the explanation is clear, thorough, and covers each point comprehensively. 
   Result must only be in Korean and should follow the specified structure.

    #Slide: 3
    #Header: title
    #Content: -subtitle  
              -content
              -content
              
    #Slide: LAST
    #Header: Summary
    #Content: -content

    ...

    Answer ONLY in this format, without any additional text


    """
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.5,
        max_tokens=4096,
    )
    result = response.choices[0].message.content.strip()
    return response.choices[0].message.content.strip()




def split_slides(ppt_text: str, index: int = 0):
    """
    ppt_text : create_ppt_text / create_ppt_detail_text 에서 받은 전체 문자열
    index    : 0이면 '요약 버전' 첫 패스, 0이 아니면 같은 파일에 디테일을 덧붙이는 패스
    """

    global SLIDE_TITLE_TEXT    # 예: '경제학자_엥겔스_과제_발표_1.ppt'
    base_dir = SLIDE_TITLE_TEXT

    # 폴더가 없으면 항상 먼저 만든다
    os.makedirs(base_dir, exist_ok=True)

    # '#Slide:' 기준으로 블록 분리
    # (맨 앞에 오는 #Title: 블록까지 포함해서 싹 자름)
    blocks = re.split(r'\n(?=#Slide:)', ppt_text.strip())
    slide_no = index

    for block in blocks:
        # 슬라이드 번호 자체는 굳이 안 써도 되지만, 필요하면 여기서 읽을 수 있음
        # slide_match = re.search(r'#Slide:\s*(\d+)', block)

        header_match = re.search(r'#Header:\s*(.+)', block)
        content_match = re.search(r'#Content:\s*((?:.|\n)+)', block)

        if not header_match or not content_match:
            # 형식 안 맞으면 그냥 건너뜀
            continue

        raw_header = header_match.group(1).strip()
        content = content_match.group(1).strip()

        # 파일 이름에 쓸 수 있게 헤더를 안전하게 정제
        safe_header = re.sub(r'[\\/:*?"<>|]', "_", raw_header)

        # 파일 경로: "{폴더}/{슬라이드번호}_{헤더}.txt"
        file_path = os.path.join(base_dir, f"{slide_no}_{safe_header}.txt")

        # index == 0이면 새 파일을 만들고, 그 이상이면 기존 파일에 내용을 붙인다
        mode = "w" if index == 0 else "a"

        with open(file_path, mode, encoding="utf-8") as f:
            if index == 0:
                # 첫 패스: 헤더에 슬라이드 번호 prefix 붙여서 한 줄 쓰고, 내용도 같이 씀
                f.write(f"{slide_no}_{raw_header}\n")
                f.write(content + "\n")
            else:
                # 두 번째 이후 패스: 빈 줄 하나 비우고 디테일만 추가
                f.write("\n" + content + "\n")

        slide_no += 1

def sanitize_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace("\n", "").replace("\r", "").strip()
    return name






def get_textlist_from_txt():
    global SLIDE_TITLE_TEXT
    dir = f'{SLIDE_TITLE_TEXT}'  # 'licenses' 폴더 경로
    text_list = []

    # 'licenses' 디렉토리 확인

    files = os.listdir(dir)
    f_index = 0
    # .txt 파일 처리
    for index, file in enumerate(files):
        if file.endswith('.txt'):
            file_path = os.path.join(dir, file)
            file = file.replace('.txt', '')
            file = file.replace('\\', '')
            file = file.replace(f'{f_index}_', '')
            text_list.append(file)
            f_index += 1

            # 파일 열고 내용 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(4000)  # 처음 1200자만 읽기
                content = content.replace('\t', '')
                text_list.append(content)

    
    return text_list



from collections import defaultdict

def group_and_sort_by_prefix(text_list: list[str]) -> list[str]:
    """
    text_list 안의 각 줄이 '0_제목...', '1_내용...' 처럼
    숫자 prefix를 가지고 있다고 가정하고,
    슬라이드 번호 순서대로 (0,1,2,3,...) 정렬해서
    각 슬라이드당 최대 2줄(제목/내용)만 돌려준다.
    번호가 없는 줄(예: '목차...')은 직전 번호 슬라이드에 붙인다.
    """

    grouped: dict[int, list[str]] = defaultdict(list)
    current_idx: int | None = None

    for line in text_list:
        stripped = line.strip()
        if not stripped:
            continue

        m = re.match(r"^(\d+)_", stripped)
        if m:
            # 새 슬라이드 번호
            current_idx = int(m.group(1))
            grouped[current_idx].append(stripped)
        else:
            # 번호가 없으면 직전 슬라이드에 내용으로 붙인다
            if current_idx is not None:
                grouped[current_idx].append(stripped)
            # current_idx 가 아직 None이면(파일 첫 줄이 번호 없이 시작했다면) 그냥 무시

    # 번호 순서대로 정렬해서, 각 슬라이드당 최대 2줄(제목+내용)만 사용
    sorted_result: list[str] = []
    for idx in sorted(grouped.keys()):
        sorted_result.extend(grouped[idx][:2])

    return sorted_result

def create_slides(original_file_id, SLIDE_TITLE_TEXT):
    global presentation_id
    creds = get_google_creds()
    SCOPES = ['https://www.googleapis.com/auth/presentations', 'https://www.googleapis.com/auth/drive']

    
    service = build('slides', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)


    try:
        presentation = drive_service.files().copy(  # 템플릿 슬라이드 복사
            fileId=f'{original_file_id}',  # template 3 원본 test_1103
            fields='id,name,webViewLink',
            body={'name': f'{SLIDE_TITLE_TEXT}'}
        ).execute()

        presentation_id = presentation['id']
        presentation_link = presentation['webViewLink']
        presentation = service.presentations().get(presentationId=presentation_id).execute()
        file_path = "presentation_data.json"
        # JSON 파일로 저장
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(presentation, json_file, ensure_ascii=False, indent=4)

        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)  # JSON을 딕셔너리 형태로 로드

        # 텍스트 파일에서 슬라이드용 텍스트 읽기
        text_list = get_textlist_from_txt()
        sorted_text_list = group_and_sort_by_prefix(text_list)
       
        
        requests_update = []
        object_index = []

        # 템플릿별로 어떤 텍스트 박스에 내용을 넣을지 결정
        # 기본값: 텍스트 파일에서 읽어온 순서를 그대로 사용
        text_list_for_mapping = list(sorted_text_list)
        # text_list_for_mapping = normalize_text_order(text_list)

        # template 1 (새 템플릿 ID)
        # 이 템플릿에서는 모든 텍스트 박스에 순서대로 채웁니다.
        if original_file_id == "1BD_IbF8x62MsUNlFGbWSmt4v7rpMR5us8BxIwmvMZ9I":
            text_list_for_mapping = list(sorted_text_list)


            for slide in presentation.get("slides", []):
                elements = slide.get('pageElements', [])

        # TEXT_BOX만 선택
                text_boxes = [
                    e for e in elements
                    if e.get("shape", {}).get("shapeType") == "TEXT_BOX"
                ]

        # 위치 기준으로 정렬 (위쪽이 먼저, 같은 높이면 왼쪽이 먼저)
                def pos(e):
                    t = e.get("transform", {})
                    return (t.get("translateY", 0), t.get("translateX", 0))

                text_boxes.sort(key=pos)

        # 제목 / 내용 2개만 사용
                for e in text_boxes[:2]:
                    object_id = e["objectId"]
                    object_index.append(object_id)

            # 디버깅용 출력
                    print(f"object_index append: slide={slide.get('objectId')}, obj={object_id}")

     

        # template 2
        elif original_file_id == '1LAsaHc6o9uzZPl0zsDfhRlt9oNWhmBEbp1vLYOU17tk':
                
                text_list.insert(4, text_list[0])
                text_list.insert(5, '1')
                text_list.insert(12, text_list[0])
                text_list.insert(13, '2')

                for slide in presentation.get('slides', []):
                    elements = slide.get('pageElements', [])
                    slide_id = slide.get('objectId')
                    print(f"Slide ID: {slide_id}:{len(elements)}")

                    for element in elements[:2]:
                        element_id = element.get('objectId')
                        object_index.append(element_id)

                        print(f"  - Element ID: {element_id}")
                print(text_list)

        # template 3
        elif original_file_id == "1QTy_L8GU-fDZV5jE9ZO5aEuW2l1eDcFa6NH5BOYR8Ak":
            text_list_for_mapping = list(text_list_for_mapping)
            text_list_for_mapping.insert(4, text_list_for_mapping[0])
            text_list_for_mapping.insert(5, "1")
            text_list_for_mapping.insert(12, text_list_for_mapping[0])
            text_list_for_mapping.insert(13, "2")

            for slide in presentation.get("slides", []):
                elements = slide.get("pageElements", [])
                if len(elements) == 3:
                    targets = elements[:2]
                else:
                    targets = elements

                for element in targets:
                    object_index.append(element.get("objectId"))

        # template 4
        elif original_file_id == "1Mohc1dhmGKbE1NALs8QRRftFK8wnJMJ-CUOMpv36Z50":
            text_list_for_mapping = text_list

            for slide in presentation.get("slides", []):
                elements = slide.get("pageElements", [])
                slide_id = slide.get("objectId")
                if slide_id in ("p2", "p6", "p9"):
                    targets = elements[1:]
                else:
                    targets = elements[:2]

                for element in targets:
                    object_index.append(element.get("objectId"))


        num_pairs = min(len(object_index), len(text_list_for_mapping))
        mapped_data = {
            object_index[i]: text_list_for_mapping[i]
            for i in range(num_pairs)
        }
        print("DEBUG: len(text_list_for_mapping) =", len(text_list_for_mapping))
        print("DEBUG: len(object_index) =", len(object_index))
        for i, oid in enumerate(object_index):
            if i < len(text_list_for_mapping):
                sample_txt = text_list_for_mapping[i]
            else:
                sample_txt = "<no text (not mapped)>"
            print(f"  [{i}] object_id={oid}, text={sample_txt[:30]}...")

        # 1) 모든 텍스트 박스 내용 초기화 (템플릿에 남아 있는 예제 텍스트 제거)
        all_text_boxes = []
        for slide in presentation.get("slides", []):
            for element in slide.get("pageElements", []):
                shape = element.get("shape")
                if not shape:
                    continue
                text = shape.get("text", {})
                text_elements = text.get("textElements", [])
                if any("textRun" in te for te in text_elements):
                    all_text_boxes.append(element["objectId"])

        for obj_id in all_text_boxes:
            requests_update.append({
                "deleteText": {
                    "objectId": obj_id,
                    "textRange": {"type": "ALL"}
                }
            })

        # 2) 템플릿 정보가 있는 경우: object_index 기반으로 매핑
        if object_index:
            try:
                mapped_data = dict(zip(object_index, text_list_for_mapping))
            except Exception:
                mapped_data = {}

            for slide in presentation.get("slides", []):
                for element in slide.get("pageElements", []):
                    obj_id = element.get("objectId")
                    if obj_id not in mapped_data:
                        continue

                    # 실제로 텍스트를 가진 shape 인지 다시 한 번 체크
                    shape = element.get("shape")
                    if not shape:
                        continue
                    text = shape.get("text", {})
                    text_elements = text.get("textElements", [])
                    has_text_run = any("textRun" in te for te in text_elements)
                    if not has_text_run:
                        # 그림/도형 등 텍스트가 없는 요소는 건너뜀
                        continue

                    content = mapped_data[obj_id] or ""

                    # 줄바꿈은 유지하되, 탭/불필요한 공백 정리
                    content = content.replace("\r\n", "\n").replace("\r", "\n")
                    content = content.replace("\t", " ")
                    lines = [
                        re.sub(r"[ ]+", " ", line).strip()
                        for line in content.split("\n")
                    ]
                    cleaned = "\n".join(lines).strip()

                    # 기존 텍스트는 위에서 한 번 모두 삭제했으므로
                    # 여기서는 새 텍스트만 삽입
                    requests_update.append({
                        "insertText": {
                            "objectId": obj_id,
                            "text": cleaned
                        }
                    })
        else:
            # 3) 템플릿 정보가 없는 경우: 모든 텍스트 박스에 순서대로 채워 넣기
            for obj_id, content in zip(all_text_boxes, text_list_for_mapping):
                content = content or ""
                content = content.replace("\r\n", "\n").replace("\r", "\n")
                content = content.replace("\t", " ")
                lines = [
                    re.sub(r"[ ]+", " ", line).strip()
                    for line in content.split("\n")
                ]
                cleaned = "\n".join(lines).strip()

                requests_update.append({
                    "insertText": {
                        "objectId": obj_id,
                        "text": cleaned
                    }
                })

        print(
            "DEBUG:",
            len(text_list_for_mapping),
            "texts,",
            len(object_index),
            "mapped_boxes,",
            len(requests_update),
            "requests",
        )
        # 3) 프레젠테이션 업데이트 요청 준비 완료
        permission = {
            "type": "anyone",  # 모든 사용자
            "role": "reader",  # 읽기 권한 (viewer)
        }

      

        slides_service = build('slides', 'v1', credentials=creds)
      
        if requests_update:
            slides_service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests_update}
            ).execute()
        else:
            print("⚠️ requests_update가 비어 있어서 batchUpdate를 건너뜁니다.")

        # 공개 링크 권한 부여
        drive_service.permissions().create(
            fileId=presentation_id,
            body=permission,
            fields="id"
        ).execute()

        return presentation_link

    except Exception as e:
        print("❌ create_slides 에러:", e)
        return None


############################################################################


@login_required
def profile(request):
    user = request.user  # 로그인한 사용자 정보

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        nickname = request.POST.get('nickname')

        # ✅ 사용자 정보 업데이트
        user.username = username
        user.email = email
        user.nickname = nickname  # ✅ CustomUser 모델의 nickname 필드 업데이트
        user.save()

        messages.success(request, "Your profile has been updated!")  # 성공 메시지
        return redirect('profile')  # 업데이트 후 같은 페이지로 리다이렉트

    # ✅ GET 요청 시 사용자 정보를 템플릿에 전달
    return render(request, 'blog/profile.html', {
        'user': user,
        'username': user.username,
        'email': user.email,
        'nickname': user.nickname,  # ✅ 닉네임 전달 확인
    })

# 서비스 계정 인증 설정
def authenticate_with_service_account():
    # 서비스 계정 JSON 파일 경로
    SERVICE_ACCOUNT_FILE = 'C:/new3_d/credentials.json'

    # 필요한 API 범위 설정
    SCOPES = ['https://www.googleapis.com/auth/presentations.readonly']

    # 서비스 계정 인증
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # API 클라이언트 생성
    service = build('slides', 'v1', credentials=creds)
    return service


# Google Slides 문서에서 첫 번째 슬라이드의 썸네일 가져오기
def get_slide_thumbnail(presentation_id, slide_index=0):
    service = authenticate_with_service_account()

    # 프레젠테이션 정보 가져오기
    presentation = service.presentations().get(presentationId=presentation_id).execute()
    # 첫 번째 슬라이드의 objectId 가져오기
    slide_object_id = presentation['slides'][slide_index]['objectId']
    # 썸네일 이미지 URL 가져오기
    thumbnail = service.presentations().pages().getThumbnail(
        presentationId=presentation_id,
        pageObjectId=slide_object_id
    ).execute()
    return thumbnail.get('contentUrl')

# 뷰에서 슬라이드 썸네일을 HTML로 렌더링
def display_slides(request):
    # 프레젠테이션 ID 목록
    global presentation_id
    slides=get_slides_list()
 
    # HTML 템플릿에 데이터를 전달
    return render(request, 'blog/result_tap.html', {'slides': slides, 'presentation_id': presentation_id})

# 로깅 설정
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/presentations.readonly']
SERVICE_ACCOUNT_FILE = 'credentials.json'  # 서비스 계정 JSON 파일

def get_google_creds(scopes=None):
    """token.json + client_secret.json 기반으로 자격 증명 가져오기"""
    if scopes is None:
        scopes = SCOPES

    creds = None

    # 1) token.json 에서 기존 자격 증명 읽기
    if os.path.exists("token.json"):
        with open("token.json", "rb") as token:
            creds = pickle.load(token)

    # 2) 없거나 만료되었으면 새로 로그인
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json",
                scopes,
            )
            creds = flow.run_local_server(port=0)

        # 3) 갱신된 자격 증명 저장
        with open("token.json", "wb") as token:
            pickle.dump(creds, token)

    return creds

def get_slides_list():
    # global SCOPES
    global presentation_id
    creds = get_google_creds()
    # 1) token.json에서 자격 증명 로드
    # if os.path.exists('token.json'):
    #     with open('token.json', 'rb') as token:
    #         creds = pickle.load(token)

    # # 2) 없거나 만료되면 새로 로그인
    # if not creds or not creds.valid:
    #     if creds and creds.expired and creds.refresh_token:
    #         creds.refresh(Request())
    #     else:
    #         flow = InstalledAppFlow.from_client_secrets_file(
    #             'client_secret.json', SCOPES
    #         )
    #         creds = flow.run_local_server(port=0)

    #     with open('token.json', 'wb') as token:
    #         pickle.dump(creds, token)

            
    """Google Drive에서 사용자의 슬라이드 목록 가져오기"""
    # creds = service_account.Credentials.from_service_account_file(
    #     SERVICE_ACCOUNT_FILE, scopes=SCOPES
    # )

    # drive_service = build('drive', 'v3', credentials=creds)
    slides_service = build('slides', 'v1', credentials=creds)

    # 프레젠테이션 정보 가져오기
    # presentation = slides_service.presentations().get(presentationId=presentation_id).execute()
    # slides = presentation.get('slides', [])
    presentation = slides_service.presentations().get(
        presentationId=presentation_id
    ).execute()
    slides = presentation.get('slides', [])

    # 첫 5개의 슬라이드만 선택
    # thumbnails = []
    # for index, slide in enumerate(slides[:5]):
    #     slide_id = slide.get('objectId')

    #     # 슬라이드 썸네일 가져오기
    #     thumbnail_response = slides_service.presentations().pages().getThumbnail(
    #         presentationId=presentation_id,
    #         pageObjectId=slide_id
    #     ).execute()

    #     thumbnails.append(thumbnail_response.get('contentUrl'))

    # return thumbnails
    thumbnails = []
    for index, slide in enumerate(slides[:5]):
        slide_id = slide.get('objectId')

        thumbnail_response = slides_service.presentations().pages().getThumbnail(
            presentationId=presentation_id,
            pageObjectId=slide_id
        ).execute()

        thumbnails.append(thumbnail_response.get('contentUrl'))

    return thumbnails


def get_slide_image(slides_service, presentation_id, page_id):
    """
    Google Slides에서 특정 슬라이드를 이미지(썸네일)로 가져오기
    :param slides_service: Google Slides API 서비스 객체
    :param presentation_id: 프레젠테이션 ID
    :param page_id: 슬라이드의 Object ID
    :return: 썸네일 URL (없으면 None)
    """
    try:
        # 특정 슬라이드의 썸네일 URL 가져오기
        thumbnail = slides_service.presentations().pages().getThumbnail(
            presentationId=presentation_id, pageObjectId=page_id
        ).execute()
        return thumbnail.get("contentUrl")

    except Exception as e:
        logger.error(f"Error getting slide image for presentation {presentation_id}, page {page_id}: {str(e)}")
        return None

def get_slide_images(presentation_id, max_slides=4):
    """
    Google Slides에서 첫 몇 개의 슬라이드 이미지를 가져오기
    :param presentation_id: 프레젠테이션 ID
    :param max_slides: 가져올 슬라이드 개수 (기본값 4)
    :return: 썸네일 URL 리스트
    """
    slides_service = authenticate_with_service_account()

    try:
        # 프레젠테이션의 모든 슬라이드 정보 가져오기
        presentation = slides_service.presentations().get(presentationId=presentation_id).execute()
        slides = presentation.get("slides", [])

        if not slides:
            logger.error(f"Presentation {presentation_id} has no slides.")
            return []

        slide_images = []

        # 지정된 개수만큼 슬라이드 이미지 가져오기
        for slide in slides[:max_slides]:
            page_id = slide["objectId"]
            image_url = get_slide_image(slides_service, presentation_id, page_id)
            if image_url:  # 유효한 이미지 URL만 추가
                slide_images.append(image_url)

        return slide_images

    except Exception as e:
        logger.error(f"Error getting slides images for presentation {presentation_id}: {str(e)}")
        return []


def download_pptx(presentation_id):
    """Google Slides 프레젠테이션을 PPTX 형식으로 다운로드"""

    try:
        # 1) OAuth 자격 증명 가져오기 (token.json 기반)
        creds = get_google_creds()

        drive_service = build("drive", "v3", credentials=creds)

        # 2) 프레젠테이션 이름 가져오기
        file_metadata = drive_service.files().get(
            fileId=presentation_id,
            fields="name",
        ).execute()
        presentation_name = file_metadata.get("name", "presentation")

        # 3) PPTX로 export
        google_request = drive_service.files().export_media(
            fileId=presentation_id,
            mimeType="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
        # 다운로드 진행
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, google_request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

        fh.seek(0)  # 파일 포인터 앞으로

        # 4) Django로 파일 전송
        response = HttpResponse(
            fh.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
        # 파일 이름 한글이면 인코딩 한 번 더 신경 써야 하지만 일단 기본 버전:
        response["Content-Disposition"] = f'attachment; filename="{presentation_name}.pptx"'
        
        return response
    except Exception as e:
        logger.error(
            f"Error downloading PPTX for presentation {presentation_id}: {str(e)}"
        )
        # 프론트에 에러 메시지 간단히 반환
        return HttpResponse("PPTX 다운로드 중 오류가 발생했습니다.", status=500)

    # try:
    #     # 인증 설정
    #     creds = service_account.Credentials.from_service_account_file(
    #         SERVICE_ACCOUNT_FILE, scopes=SCOPES
    #     )
    #     drive_service = build("drive", "v3", credentials=creds)

    #     # 프레젠테이션 정보 가져오기 (파일명 확인)
    #     file_metadata = drive_service.files().get(fileId=presentation_id, fields="name").execute()
    #     presentation_name = file_metadata.get("name", "presentation")

    #     # 파일을 PPTX로 다운로드
    #     google_request = drive_service.files().export_media(
    #         fileId=presentation_id,
    #         mimeType="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    #     )

    #     # 다운로드 진행
    #     fh = io.BytesIO()
    #     downloader = MediaIoBaseDownload(fh, google_request)
    #     done = False
    #     while not done:
    #         status, done = downloader.next_chunk()

    #     fh.seek(0)  # 파일 포인터를 처음으로 이동

    #     with open(f"{presentation_name}.pptx", "wb") as f:
    #         f.write(fh.read())

    #     # Django 환경이면 HttpResponse 반환
    #     if HttpResponse:
    #         response = HttpResponse(
    #             fh, content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    #         )
    #         response["Content-Disposition"] = f'attachment; filename="{presentation_name}.pptx"'
           
    #         return response

    # except Exception as e:
    #     logger.error(f"Error downloading PPTX for presentation {presentation_id}: {str(e)}")
    #     raise



logger = logging.getLogger(__name__)

def download_slide(request, presentation_id):
    # global presentation_id
    # print("\n")
    # print(f"{presentation_id}: in download_slide")
    """Google Drive에서 파일을 직접 다운로드"""
    # if not presentation_id:
    #     logger.error("Error: Missing presentation_id in download_slide view")
    #     return HttpResponse("Error: Missing presentation_id", status=400)

    try:
        # logger.info(f"Starting download_pptx for {presentation_id}")
        # response = download_pptx(presentation_id) #원본
        download_pptx(presentation_id)
        # 프레젠테이션 다운로드
        # pptx_file = download_pptx(presentation_id)
        # print(f"download_pptx_result: {pptx_file}")
        #
        # # HTTP 응답 설정
        # response = HttpResponse(pptx_file, content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation')
        # response['Content-Disposition'] = f'attachment; filename={presentation_id}.pptx'
        # print(f"response about download{response}")
        # logger.info(f"Response type: {type(response)}")
        # return HttpResponse("File downloaded successfully!")
        return redirect('result')

    except Exception as e:
        # 에러 로그 기록
        logger.error(f"Error in download_slide for presentation {presentation_id}: {str(e)}")
        return HttpResponse(f"Error downloading the presentation: {str(e)}", status=500)



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# @csrf_exempt  # CSRF 검사를 비활성화 (테스트용, 실제 서비스에서는 CSRF 토큰을 활용)
# def chat_view(request):
#     if request.method == "POST":
#         user_message = request.POST.get("user-input", "")
#
#         # 예제: 간단한 응답 로직
#         if user_message.lower() == "안녕":
#             bot_reply = "안녕하세요! 어떻게 도와드릴까요?"
#         else:
#             bot_reply = "말씀하신 내용을 확인 중입니다."
#
#         return JsonResponse({"reply": bot_reply})
#
#     return JsonResponse({"error": "Invalid request"}, status=400)
