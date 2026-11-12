"""숨틈 · 금연 동행 — streamlit run quit_app.py
GitHub에 이 파일과 requirements.txt 업로드 → Streamlit Cloud 실행 파일 quit_app.py.
기본 저장: 로컬 SQLite. Cloud 재배포·서버 초기화 시 사라질 수 있습니다.
영구 저장 선택: Supabase SQL Editor에서 아래 실행:
create table public.quit_accounts (id text primary key,payload jsonb not null,version integer not null default 0);
alter table public.quit_accounts enable row level security;
-- 공개 접근 정책을 추가하지 마세요. 서버만 접근합니다.
Streamlit Settings > Secrets (키를 GitHub에 올리지 마세요):
SUPABASE_URL="https://프로젝트.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="서버 전용 service_role 키"
정보 출처: 국가금연지원서비스 https://nosmokeguide.go.kr / 금연상담전화 1544-9030
건강 회복 시점·수명 연장 등의 개인별 의학 수치를 추정하지 않습니다.
"""
import streamlit as st
import streamlit.config as config
import requests,sqlite3,json,secrets,hashlib,time,html
from datetime import datetime,date,timedelta
from zoneinfo import ZoneInfo
for k,v in {'theme.base':'light','theme.primaryColor':'#367545','theme.backgroundColor':'#F0F7EA','theme.secondaryBackgroundColor':'#FFFFFF','theme.textColor':'#244632'}.items():
    config.set_option(k,v)
st.set_page_config(page_title='숨틈 · 금연 동행',page_icon='🌿',layout='centered')
TZ=ZoneInfo('Asia/Seoul')
def now(): return datetime.now(TZ)
def hashed(s):return hashlib.sha256(s.encode()).hexdigest()
def pw(p,s):return hashlib.pbkdf2_hmac('sha256',p.encode(),bytes.fromhex(s),180000).hex()
def remote():
    try:return bool(st.secrets.get('SUPABASE_URL') and st.secrets.get('SUPABASE_SERVICE_ROLE_KEY'))
    except Exception:return False
def db(key,data=None,version=None):
    if remote():
        root=st.secrets['SUPABASE_URL'].rstrip('/')+'/rest/v1/quit_accounts'
        headers={'apikey':st.secrets['SUPABASE_SERVICE_ROLE_KEY'],'Authorization':'Bearer '+st.secrets['SUPABASE_SERVICE_ROLE_KEY'],'Prefer':'return=representation'}
        if data is None:
            r=requests.get(root,params={'id':'eq.'+key},headers=headers,timeout=20);r.raise_for_status();rows=r.json()
            return (rows[0]['payload'],rows[0]['version']) if rows else (None,None)
        if version is None:
            r=requests.post(root,headers=headers,json={'id':key,'payload':data,'version':0},timeout=20)
        else:
            r=requests.patch(root,params={'id':'eq.'+key,'version':'eq.'+str(version)},headers=headers,json={'payload':data,'version':version+1},timeout=20)
        r.raise_for_status()
        if not r.json():raise ValueError('다른 화면에서 변경됐어요. 새로고침 후 다시 해 주세요.')
        return
    with sqlite3.connect('quit_data.sqlite3',timeout=20) as c:
        c.execute('create table if not exists accounts(id text primary key,payload text,version integer not null)')
        if data is None:
            row=c.execute('select payload,version from accounts where id=?',(key,)).fetchone()
            return (json.loads(row[0]),row[1]) if row else (None,None)
        if version is None:c.execute('insert into accounts values(?,?,0)',(key,json.dumps(data)))
        else:
            q=c.execute('update accounts set payload=?,version=version+1 where id=? and version=?',(json.dumps(data),key,version))
            if q.rowcount!=1:raise ValueError('다른 화면에서 변경됐어요. 새로고침 후 다시 해 주세요.')
def save(d,v):db(st.session_state.uid,d,v);st.rerun()
def elapsed(start,end):return max(0,(end-start).total_seconds())
def estimates(start,end,cigs,price,pack):
    days=elapsed(start,end)/86400
    return days*cigs,days*cigs*price/pack
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');
:root{color-scheme:light!important}
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:#F0F7EA!important;color:#244632!important}
[data-testid="stHeader"]{background:#F0F7EA!important;height:2.8rem!important;border-bottom:1px solid #DAE7D1}
.block-container{max-width:540px!important;padding:4.2rem 1rem 2rem!important}
h1,h2,h3{font-family:'Jua','Apple SD Gothic Neo',sans-serif!important;color:#285738!important}
p,label,li,small,[data-testid="stCaptionContainer"] p,[data-testid="stWidgetLabel"] p{color:#355640!important}
.warning{border-radius:24px;padding:22px;background:#DDEFCF!important;color:#244632!important;border:2px solid #BED8A9;margin:12px 0 16px;box-shadow:0 4px 0 #D0E3C1}
.warning small{color:#456A39!important;letter-spacing:1px;font-weight:700}.warning h2{font-size:29px!important;margin:10px 0;color:#285738!important}.warning p{color:#355640!important;font-size:14px;margin:0}
.score{background:#FFFFFF!important;border-radius:23px;padding:18px 22px;margin:14px 0;border:1px solid #CDDFC3;color:#355640!important}.score strong{font-family:'Jua',sans-serif;font-size:46px;color:#397946!important}.score span{color:#45624B!important;font-size:14px}
[data-testid="stAlert"],[data-testid="stAlertContainer"],div[role="alert"]{background:#E2F0D9!important;border:1px solid #AEC99B!important;border-radius:16px!important;color:#274D34!important}
[data-testid="stAlert"] *,[data-testid="stAlertContainer"] *,div[role="alert"] *{color:#274D34!important;fill:#397946!important}
[data-testid="stExpander"], [data-testid="stExpander"] details,[data-testid="stExpander"] summary,[data-testid="stExpander"] summary:hover{background:#FAFDF6!important;border-radius:15px!important;color:#31563B!important}
[data-testid="stExpander"]{border:1px solid #C8DDBB!important;margin:10px 0!important}
[data-testid="stExpander"] summary *{color:#31563B!important}
input,textarea,[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="select"]>div,[data-testid="stNumberInputContainer"]{background:#FFFFFF!important;color:#254C34!important;-webkit-text-fill-color:#254C34!important}
input::placeholder{color:#637B62!important;-webkit-text-fill-color:#637B62!important}
[data-testid="stNumberInput"] button{background:#E2EFD8!important;color:#31563B!important}
button[kind="primary"],button[kind="primaryFormSubmit"]{background:#367545!important;border:1px solid #2B6439!important;color:white!important;min-height:60px!important;border-radius:17px!important}
button[kind="primary"] *,button[kind="primaryFormSubmit"] *{color:white!important}
button[kind="secondary"],button[kind="secondaryFormSubmit"],[data-testid="stDownloadButton"] button,[data-testid="stLinkButton"] a{background:#FFFFFF!important;border:1px solid #AEC99B!important;color:#31563B!important;min-height:46px!important;border-radius:14px!important}
button[kind="secondary"] *,button[kind="secondaryFormSubmit"] *,[data-testid="stDownloadButton"] button *,[data-testid="stLinkButton"] a *{color:#31563B!important}
button:disabled{opacity:.55!important}
[data-testid="stMetric"]{background:#FFFFFF!important;border:1px solid #CDDFC3!important;padding:14px!important;border-radius:18px!important}
[data-testid="stMetric"] *{color:#31563B!important}
[data-testid="stForm"]{background:#FAFDF6!important;border:1px solid #C8DDBB!important;border-radius:19px!important}
[role="radiogroup"]{background:#E0EED6!important;padding:9px!important;border-radius:15px!important}
[role="radiogroup"] *{color:#31563B!important}
[role="dialog"],[role="listbox"],[role="option"],[data-baseweb="calendar"]{background:#FFFFFF!important;color:#31563B!important}
[data-testid="stCode"],pre,code{background:#FFFFFF!important;color:#254C34!important}
</style>''',unsafe_allow_html=True)
try:
    # 개인 기기에 보관하는 접근 코드. URL/QR에 인증 정보를 넣지 않습니다.
    if 'uid' not in st.session_state:
        st.markdown('<div class="warning"><small>🌿 나의 금연 새싹</small><h2>담배 한 개비,<br>기록은 한 번의 터치.</h2><p>흡연 기록 · 다음 한 개비 미루기</p></div>',unsafe_allow_html=True)
        mode=st.radio('시작',['바로 시작','기록 불러오기','아이디 찾기'],horizontal=True,label_visibility='collapsed')
        if mode=='바로 시작':
            st.caption('이메일·비밀번호 입력 없이 개인 코드를 발급해요.')
            if st.button('내 기록 만들기',type='primary',use_container_width=True):
                code=secrets.token_hex(16).upper();uid='quick_'+hashed(code)
                db(uid,{'username':'숨틈-'+code[:6],'logs':[],'recovery':hashed(code)})
                st.session_state.uid=uid;st.session_state.fresh_code=code;st.rerun()
        else:
            with st.form('restore'):
                code=st.text_input('처음 발급받은 개인 코드',type='password')
                submit=st.form_submit_button('아이디 확인' if mode=='아이디 찾기' else '내 기록 열기',use_container_width=True)
            if submit:
                uid='quick_'+hashed(code.strip().upper());account,_=db(uid)
                if not account:st.error('코드를 확인해 주세요. 이전 버전 계정은 자동 이전되지 않아요.')
                elif mode=='아이디 찾기':st.success('내 아이디: '+account['username'])
                else:st.session_state.uid=uid;st.rerun()
            st.caption('개인 코드를 잃으면 복구할 수 없어요. 다른 사람과 공유하지 마세요.')
        if not remote():st.caption('체험 저장 · 서버 초기화 시 기록이 사라질 수 있어요.')
        st.stop()
    d,v=db(st.session_state.uid)
    if not d:st.session_state.clear();st.rerun()
    if st.session_state.get('fresh_code'):
        st.info('한 번만 보이는 개인 코드예요. 안전한 곳에 보관하세요.')
        st.code(st.session_state.fresh_code)
        st.caption('다시 접속하거나 아이디를 찾을 때 필요해요. 이 코드를 아는 사람은 기록을 볼 수 있어요.')
        if st.button('코드 보관했어요'):st.session_state.pop('fresh_code');st.rerun()
        st.stop()
    if not d.get('smoking_profile'):
        st.subheader('흡연 이력 · 처음 한 번만')
        with st.form('smoking_profile'):
            age=st.number_input('현재 나이 (만 나이)',min_value=1,max_value=110,value=30)
            years=st.number_input('흡연한 기간 (년)',min_value=0.0,max_value=100.0,value=5.0,step=0.5)
            average=st.number_input('그동안 하루 평균 개비',min_value=1,max_value=200,value=10)
            started=st.form_submit_button('저장하고 시작',type='primary',use_container_width=True)
        if started:
            if years>age:
                st.error('흡연 기간이 나이보다 길 수 없어요.')
            else:
                d['smoking_profile']={'age':age,'years':years,'average':average,'recorded_at':now().isoformat()}
                save(d,v)
        st.stop()
    with st.expander('⚠ 흡연으로 위험이 높아지는 질환', expanded=False):
        st.markdown('**암**')
        st.write('폐암 · 구강암 · 인두암 · 후두암 · 식도암 · 위암 · 췌장암 · 간암 · 대장·직장암 · 신장암 · 방광암 · 자궁경부암 · 급성골수성백혈병')
        st.markdown('**심장·혈관 / 호흡기**')
        st.write('관상동맥질환 · 뇌졸중 · 말초동맥질환 · 만성폐쇄성폐질환(COPD)')
        st.caption('흡연과 인과관계가 확인된 대표 질환입니다. 흡연한다고 반드시 생기는 것은 아니며 개인 진단이나 발생 확률을 뜻하지 않아요.')
        st.caption('가족의 흡연 기록은 개인 건강정보예요. 개인 코드는 공유하지 마세요.')
        st.link_button('근거 보기 · 미국 CDC', 'https://www.cdc.gov/tobacco/about/index.html')
    st.markdown('<div class="warning"><small>🌱 ONE LITTLE STEP</small><h2>다음 한 개비 대신,<br>작은 숨틈 🌿</h2><p>기록은 한 번의 터치, 금연은 한 걸음씩.</p></div>',unsafe_allow_html=True)
    current=now();today=str(current.date());logs=d.get('logs',[])
    today_logs=[x for x in logs if datetime.fromisoformat(x['at']).date()==current.date()]
    st.markdown(f'<div class="score"><span>오늘 기록한 흡연</span><br><strong>{len(today_logs)}</strong> 개비</div>',unsafe_allow_html=True)
    if st.button('＋ 방금 1개비 피웠어요',type='primary',use_container_width=True):
        d['logs'].append({'at':now().isoformat(),'id':secrets.token_hex(8)});st.session_state.just_smoked=True;save(d,v)
    profile=d['smoking_profile']
    # 갑년: 과거 자기보고 평균 기준. 앱 기록을 중복 가산하지 않습니다.
    pack_years=profile['average']/20*profile['years']
    st.caption(f"만 {profile['age']}세 · 흡연 {profile['years']:g}년 · 과거 흡연량 {pack_years:.1f}갑년")
    if st.session_state.pop('just_smoked',False):
        messages=[
            '담배 연기에는 발암물질이 포함돼요. 한 개비도 안전한 선택은 아니에요.',
            '흡연은 폐암뿐 아니라 심장과 혈관 건강에도 해를 줍니다.',
            '흡연은 만성폐쇄성폐질환(COPD)의 주요 원인입니다.',
            '지금 멈추는 선택은 의미가 있어요. 다음 한 개비를 미뤄 보세요.'
        ]
        st.warning(messages[(len(logs)-1)%len(messages)])
    c1,c2=st.columns(2)
    if c1.button('↶ 마지막 기록 취소',disabled=not logs,use_container_width=True):
        d['logs'].pop();save(d,v)
    if c2.button('✋ 다음 담배 3분 미루기',use_container_width=True):st.session_state.pause_end=time.time()+180
    @st.fragment(run_every='1s')
    def timer():
        if st.session_state.get('pause_end'):
            left=max(0,int(st.session_state.pause_end-time.time()))
            st.metric('물 한 모금 · 잠깐 자리 바꾸기',f'{left//60:02}:{left%60:02}')
            if left==0:st.success('3분을 미뤘어요. 가능하면 조금 더 미뤄 보세요.')
        elif logs:
            mins=max(0,int((now()-datetime.fromisoformat(logs[-1]['at'])).total_seconds()//60))
            st.caption(f'마지막으로 기록한 흡연 후 {mins//60}시간 {mins%60}분 · 미기록 흡연은 반영되지 않아요.')
    timer()
    with st.expander('최근 기록'):
        yesterday=current.date()-timedelta(days=1)
        prev=sum(datetime.fromisoformat(x['at']).date()==yesterday for x in logs)
        st.write(f'오늘 {len(today_logs)}개비 · 어제 {prev}개비')
        for x in reversed(logs[-15:]):st.write(datetime.fromisoformat(x['at']).strftime('%m/%d %H:%M')+' · 1개비')
        if not logs:st.caption('아직 기록이 없어요.')
    with st.expander('도움 · 내 계정'):
        st.write('내 아이디: '+d['username'])
        if st.button('나이·흡연 이력 수정'):
            d.pop('smoking_profile',None);save(d,v)
        st.link_button('공식 금연 도움 받기', 'https://nosmokeguide.go.kr',use_container_width=True)
        st.write('금연상담전화 1544-9030')
        st.caption('기록만으로 금연 효과를 보장하지 않아요. 금단 증상이나 금연 치료는 전문가와 상담하세요. 흉통·심한 호흡곤란은 119.')
        st.download_button('기록 내려받기',json.dumps({'username':d['username'],'logs':logs},ensure_ascii=False,indent=2),file_name='흡연기록.json',mime='application/json')
        if not remote():st.caption('현재 임시 저장. 영구 저장 설정은 파일 맨 위를 확인하세요.')
        if st.button('로그아웃'):st.session_state.clear();st.rerun()
except (requests.RequestException,sqlite3.Error,ValueError,KeyError,TypeError):
    st.error('기록을 불러오거나 저장하지 못했어요. 새로고침 후 다시 시도해 주세요.')
