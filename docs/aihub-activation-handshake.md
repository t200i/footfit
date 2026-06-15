# ITRI AI Hub ??å®¹å™¨?ˆæ?äº¤æ¡?”å?

?¬æ?ä»¶èªª??ITRI AI Hub ??Docker Model Image ä¹‹é??„ä?æ®µå?äº¤æ¡æ©Ÿåˆ¶ï¼ˆThree-Phase Handshakeï¼‰ã€? 
æ­¤æ??¶åœ¨ä¿æ? **`docker pull` + `docker run` ç°¡å–® UX** ?„å??ä?ï¼Œå? License Key ç¶å??³å”¯ä¸€è¨­å??‡ç?ï¼Œä»»ä½•æ?ç´‹ä?ç¬¦ç??·è?è«‹æ??‡è¢«?’ç???

å®Œæ?é¦–æ¬¡?Ÿç”¨ç´„é? **30 ç§?*ï¼ˆè‡ª?•åœ¨?Œæ™¯?·è?ï¼Œä?å½±éŸ¿?¨è??å??Ÿå?ï¼‰ã€?

---

## ä½¿ç”¨?…é?é©—ï?User-Facing UXï¼?

Licensee ?ªé??šå…©ä»¶ä?ï¼?

```bash
# æ­¥é?ä¸€ï¼šè¨­å®?License Keyï¼ˆä?æ¬¡æ€§ï?å»ºè­°å¯«å…¥ ~/.bashrc ??~/.zshrcï¼?
export AIHUB_LICENSE_KEY=lic-xxxxxxxxxxxxxxxx

# æ­¥é?äºŒï??‰å?ä¸¦åŸ·è¡?
docker pull model-cards.azurecr.io/amd/rocm/gemma4-4b:latest
docker run --rm -p 8000:8000 \
  -e AIHUB_LICENSE_KEY \
  model-cards.azurecr.io/amd/rocm/gemma4-4b:latest
```

?Ÿå?å¾Œï??å??³å¯?¥å? OpenAI ?¸å®¹ API è«‹æ?ï¼?

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma4-4b-gpu","messages":[{"role":"user","content":"ä½ å¥½"}]}'
```

?€?‰æ?æ¬Šé?è­‰ã€è¨­?™ç?å®šã€ç”¨?å??±å??¨å®¹?¨å…§?¨è‡ª?•è??†ï?**ä½¿ç”¨?…ä??€è¦ä?è§?º¤?¡ç´°ç¯€**??

---

## è¨­è??®æ?

| ?®æ? | æ©Ÿåˆ¶ |
|------|------|
| ç°¡å–® UX | ä¸€?‹ç’°å¢ƒè???`AIHUB_LICENSE_KEY`ï¼Œç„¡?€?›è? Volume |
| ä¸€ Key ä¸€è¨­å? | License Key ?¼é?æ¬¡å??¨æ?ç¶å?è¨­å??‡ç?ï¼ˆCPU_ID + MAC + hostnameï¼‰ï??‡ç?ä¸ç¬¦ä¸€å¾‹æ?çµ?|
| ?¢ç?å®¹éŒ¯ | ?æ?æ¬Šé›¢ç·šé?åº¦ï?Offline Budgetï¼‰é??¶é›¢ç·šæ??“æ?å¤§ç”¨?ï??°æ??ªå??œæ? |
| ?²é?å»ºæ”»??| ?æ–° Activation ??Hub ?¨é???™¤ä¸Šä?ä»?offline_budgetï¼Œé?å»ºè?å¤šæ‰£è¶Šå? |
| ?™é?å¸³æœ¬ | ä½¿ç”¨?…æ???Budgetï¼ˆâ?tokensï¼‰ï?æ¨¡å??æ??…ç²å¾?Creditï¼?tokensï¼‰ï??©æ??¨ç??’è? |
| ?ˆæ??±æ? | License Key ä»¥å¹´ï¼å­£ï¼æ??ºé€±æ??¼è?ï¼Œåˆ°?Ÿå??¯ç”³è«‹ç?ç´?|

---

## ?™é?å¸³æœ¬æ©Ÿåˆ¶ï¼ˆDual-Ledgerï¼?

æ¯ä?ç­†æ¨è«–è?æ±‚åœ¨ Hub ç«¯å??‚æ›´?°å…©?‹å¸³?¬ï?

```
ä¸€æ¬¡æ¨è«–è?æ±‚ï?æ¶ˆè€?N tokensï¼?
    ??
    ?œâ? ä½¿ç”¨?…å¸³?¬ï?Deployer Budgetï¼?
    ??      ?”â? quota_tokens_remaining ?’N
    ??           ??æ´»è?åº¦æ?è¡Œï?èª°ç”¨?€å¤šï?
    ??
    ?”â? æ¨¡å??æ??…å¸³?¬ï?Model Owner Creditï¼?
            ?”â? credit_tokens_earned +N
                 ??è²¢ç»åº¦æ?è¡Œï?èª°ç?æ¨¡å??€?—æ­¡è¿ï?
```

| è§’è‰² | å¸³æœ¬ | ?’è??‡æ? |
|------|------|---------|
| **?¨ç½²?…ï?Deployerï¼?* | Budgetï¼šæ?æ¬Šé€±æ??§å¯æ¶ˆè€—ç? token ç¸½é? | æ´»è?åº¦æ?è¡Œï?æ¶ˆè€—è?å¤šæ?è¶Šé?ï¼?|
| **æ¨¡å??æ??…ï?Model Ownerï¼?* | Creditï¼šæ?ä¸‹æ¨¡?‹è¢«æ¶ˆè€—ç?ç´¯è? token ??| è²¢ç»åº¦æ?è¡Œï?è¢«ç”¨è¶Šå??’è?é«˜ï? |

> **Model Card ä¸­ç? `model_owner_account` æ¬„ä?**æ±ºå? Credit æ­¸å±¬?‚æ?å¼µæ¨¡?‹å¡ä¸Šç??‚å³?–å?æ­¤æ?ä½ï?ä¸å¯äº‹å?ä¿®æ”¹??

---

## ä¸‰æ®µå¼äº¤?¡æ?ç¨?

### Phase 0 ???°å?æº–å?ï¼ˆä½¿?¨è€…å´ï¼Œä?æ¬¡æ€§ï?

```
ä½¿ç”¨?…è¨­å®šç’°å¢ƒè???
    ?”â??€ export AIHUB_LICENSE_KEY=lic-xxxxxxxxxxxxxxxx
         ?”â??€ docker run -e AIHUB_LICENSE_KEY ...
              ?”â??€ å®¹å™¨å¾ç’°å¢ƒè??¸è???Keyï¼Œé€²å…¥ Phase 1
```

---

### Phase 1 ???Ÿå??Ÿç”¨ï¼ˆActivation Handshakeï¼?

> **è§¸ç™¼?‚æ?**ï¼šå®¹?¨æ?æ¬¡å??•æ??·è?ä¸€æ¬?

```mermaid
sequenceDiagram
    participant E as å®¹å™¨<br/>entrypoint.sh
    participant H as AI Hub<br/>activation.ai-hub.itri.org.tw

    Note over E: 1. è¨ˆç?è¨­å??‡ç?<br/>SHA256(CPU_ID + MAC + hostname)

    E->>H: 2. POST /v1/activate<br/>{ license_key, device_fingerprint,<br/>  model_id, container_image }

    Note over H: é©—è? license_key ?‰æ???br/>æ¯”å?ç¶å???device_fingerprint<br/>ï¼ˆé?æ¬¡å??¨å?å¯«å…¥ç¶å?ï¼?br/> å¾Œç??Ÿç”¨?€å®Œå…¨?»å?ï¼?

    alt ?Ÿç”¨?å?ï¼ˆfingerprint ?»å??–é?æ¬¡ç?å®šï?
        Note over H: ?¥ä?æ¬?offline_budget å°šæœªçµç?<br/>???¨é???™¤ï¼ˆé˜²?å»º?»æ?ï¼?br/>?æ ¸?¼æ–° session_token
        H-->>E: 3. 200 OK<br/>{ session_token (è¨˜æ†¶é«”æš«å­?,<br/>  quota_tokens_remaining,<br/>  heartbeat_interval_seconds: 300,<br/>  offline_budget_tokens: 10000,<br/>  offline_budget_expires_in: 1800,<br/>  license_period: "monthly"|"quarterly"|"annual",<br/>  license_expires_at: "2026-07-15T00:00:00Z" }
        Note over E: 4. ?Ÿå??¨è??å?ï¼ˆapi.pyï¼?
    else ?Ÿç”¨å¤±æ?
        H-->>E: 4xx { error, message }
        Note over E: ?°å‡º?¯èª¤è¨Šæ¯ï¼Œexit 1
    end
```

**?Ÿç”¨å¤±æ??„æ?æ³ï?**

| ?¯èª¤ç¢?| ?Ÿå? | å®¹å™¨è¡Œç‚º |
|--------|------|---------|
| `LICENSE_INVALID` | Key ä¸å??¨æ?å·²æ’¤??| ?°å‡º?¯èª¤è¨Šæ¯ï¼Œexit 1 |
| `LICENSE_EXPIRED` | Key å·²é???| ?°å‡º?°æ??¥ï?exit 1 |
| `DEVICE_MISMATCH` | è¨­å??‡ç??‡ç?å®šç??„ä?ç¬¦ï?Key å·²ç?å®šè‡³?¦ä??°è¨­?™ï? | ?°å‡º?¯èª¤è¨Šæ¯ï¼Œæ?ç¤ºè¯çµ?AI Hub è§??ï¼Œexit 1 |
| `MODEL_NOT_PERMITTED` | æ­?Key ä¸å?è¨±åŸ·è¡Œæ­¤æ¨¡å? | ?—å‡ºè¨±å¯?„æ¨¡?‹æ??®ï?exit 1 |

---

### Phase 2 ??å®šæ?å¿ƒè·³ï¼ˆHeartbeatï¼?

> **è§¸ç™¼?‚æ?**ï¼šæ¨è«–æ??™å??•å?ï¼Œæ? `heartbeat_interval_seconds`ï¼ˆé?è¨?5 ?†é?ï¼‰åŸ·è¡Œä?æ¬?

```mermaid
sequenceDiagram
    participant E as å®¹å™¨<br/>?Œæ™¯ async task
    participant H as AI Hub

    loop æ¯?heartbeat_interval_secondsï¼ˆé?è¨?300sï¼?
        E->>H: POST /v1/heartbeat<br/>{ session_token, device_fingerprint,<br/>  seq_no, usage: { input_tokens, output_tokens, request_count } }
        Note over H: é©—è? session_token<br/>ç¢ºè? device_fingerprint ?ªè???br/>æ¯”å?ä¼ºæ??¨ç«¯å¸³æœ¬??last_confirmed_seq_no<br/>ç´¯è??¨é?ï¼Œæ›´?°å¸³?¬è??é?é¤˜é?
        H-->>E: { continue: true,<br/>  quota_tokens_remaining,<br/>  last_confirmed_seq_no,<br/>  next_heartbeat_seconds }
    end
```

**å¿ƒè·³ä¸­æ–·?„è??†ï??æ?æ¬Šé›¢ç·šé?åº¦æ??¶ï?ï¼?*

> **è¨­è??Ÿå?**ï¼šHub ?¯å”¯ä¸€å¸³æœ¬?‚é›¢ç·šæ??“ï?å®¹å™¨?ªèƒ½æ¶ˆè€—ã€Œå·²?å??ˆæ??„é›¢ç·šé?åº¦ã€ï?ä¸ä?è³´æœ¬?°è??„ç??¨é?æº–ç¢º?§ã€?

æ¯æ¬¡å¿ƒè·³?æ?ä¸­ï?Hub ?Œæ?ä¸‹ç™¼ä¸‹ä??‹å?è·³é€±æ???*?æ?æ¬Šé›¢ç·šé?åº¦ï?Offline Budgetï¼?*ï¼?

```mermaid
sequenceDiagram
    participant E as å®¹å™¨
    participant H as AI Hub

    E->>H: POST /v1/heartbeat<br/>{ session_token, seq_no,<br/>  usage_this_period: { input, output } }
    Note over H: ??™¤?¬æ??¨é?<br/>?´æ–°ä¼ºæ??¨ç«¯å¸³æœ¬<br/>?¸ç?ä¸‹ä??Ÿé›¢ç·šé?åº?
    H-->>E: { continue: true,<br/>  quota_remaining,<br/>  offline_budget_tokens: 10000,<br/>  offline_budget_expires_in: 1800 }
    Note over E: å°?offline_budget å­˜å…¥è¨˜æ†¶é«?
```

```mermaid
flowchart TD
    A([Hub ä¸å¯?”]) --> B["ä½¿ç”¨è¨˜æ†¶é«”ä¸­??offline_budget_tokens"]
    B --> C{offline_budget_tokens > 0\nä¸”å??ªåˆ°??}
    C -- ??--> D[?è¨±?¨è?\næ¯æ¬¡???æ¶ˆè€—é?]
    C -- ??--> E([?œæ­¢?å? HTTP 503\nç­‰å??é€???ç?è£œç™¼])
    D --> F{æ¯?60 ç§’é?è©¦é€??}
    F -- ????¢å¾© --> G["?å‡º?¬æ?å¯¦é??¨é?\nHub ??¸³ + è£œç™¼??offline_budget\n?¢å¾©æ­?¸¸ Heartbeat ?±æ?"]
    F -- ä»é›¢ç·?--> C
```

**?ºä?éº¼é€™æ¨£è¨­è??¯å??¨ç?ï¼?*

| ?»æ??…å? | ç³»çµ±?æ? |
|---------|---------|
| ä½¿ç”¨?…åˆª??Named Volume | offline_budget ?¨è??¶é?ä¸­ï?ä¸å?å½±éŸ¿ï¼›Hub å¸³æœ¬ä¸è? |
| ä½¿ç”¨?…ä¿®??Volume ä¸­ç??«å?ç´€??| Hub ?¨é???™¤ offline_budgetï¼Œä??¡ä¿¡å®¢æˆ¶ç«¯å??±æ•¸å­?|
| ä½¿ç”¨?…è?å®¹å™¨æ°¸é??¢ç?ä¸é???| offline_budget ?‰åˆ°?Ÿæ??“ï?`offline_budget_expires_in`ï¼‰ï??°æ?å¾Œå???|
| ä½¿ç”¨?…ä???`docker run --rm` ?å»º | æ¯æ¬¡?æ–° Activationï¼ŒHub ?¨é???™¤ä¸Šä?ä»?budget ??**?å»ºè¶Šå????å¤šï??¡æ??²åˆ©** |
| ä½¿ç”¨?…ç???Volume å°‘å ±?¨é? | Hub ä¸æ¡ä¿¡å®¢?¶ç«¯?¸å?ï¼Œçµ±ä¸€ä»¥ã€Œoffline_budget ?¨æ•¸æ¶ˆè€—å??è?å¸?|

**Named Volume ?¨æ­¤è¨­è?ä¸­å·²ä¸é?è¦ã€?*

?€?‰è?è²»é?è¼¯å???Hub ä¼ºæ??¨ç«¯å¸³æœ¬æ±ºå?ï¼Œå®¢?¶ç«¯ä¸ä?å­˜ä»»ä½•æ??ˆç?è¨ˆè²»?€?‹ï?
- offline_budget å­˜æ–¼å®¹å™¨è¨˜æ†¶é«”ï?å®¹å™¨?œæ­¢?³æ?æ»?
- Hub ?¨ä?æ¬?Activation ?‚å…¨é¡æ‰£?¤ä?ä¸€ä»?budgetï¼Œä??€è¦å®¢?¶ç«¯ä»»ä??ä??–è???

---

### Phase 3 ???è?æ±‚é?é¡é˜²è­·ï?Per-Request Guardï¼?

> **è§¸ç™¼?‚æ?**ï¼šæ?æ¬¡æ¨è«–è?æ±‚é€²å…¥ `api.py` ?‚ï??¨æ¨¡?‹æ¨è«–å?æª¢æŸ¥

```mermaid
flowchart TD
    A([?¨è?è«‹æ??²å…¥]) --> B{quota_tokens_remaining > 0?}
    B -- ??--> C[?·è?æ¨¡å??¨è?]
    C --> D[???æ¶ˆè€—ç? token ?¸]
    D --> E([?å‚³?¨è?çµæ?])
    B -- ??--> F([HTTP 429\nerror: quota_exceeded\ncontact: ai-hub@itri.org.tw])
```

---

## è¨­å??‡ç?ï¼ˆDevice Fingerprintï¼‰è?ç®—æ–¹å¼?

è¨­å??‡ç??±å®¹?¨å…§?¨è?ç®—ï?ä¸é?è¦ä½¿?¨è€…æ?ä½œï?

```python
import hashlib, platform, uuid

def compute_device_fingerprint() -> str:
    """
    çµ„å?å¤šå€‹ç¡¬é«”è??¥ç¢¼ï¼Œå? MAC ä½å??°å?ï¼ˆå? VPN?å®¹?¨ç¶²è·¯é?å»ºï??‰ä?å®šå®¹å¿åº¦??
    ?€çµ‚ç??œç‚º SHA256 hex digestï¼?4 å­—å?ï¼‰ã€?
    """
    components = []

    # CPU åºè?ï¼ˆLinux: /proc/cpuinfoï¼ŒWindows: wmicï¼?
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if "Serial" in line or "Hardware" in line:
                    components.append(line.strip())
    except Exception:
        pass

    # ä¸»æ??ç¨±ï¼ˆç©©å®šè??¥ç¬¦ï¼?
    components.append(platform.node())

    # ç¬¬ä??‹é? loopback MACï¼ˆè??›ç‚ºå­—ä¸²?¿å?æ¯æ¬¡?Ÿå?æ¼‚ç§»ï¼?
    mac = uuid.getnode()
    if mac != uuid.getnode():  # ?¥æ?æ¬¡ä??Œï??›æ“¬ MACï¼‰å??¥é?
        pass
    else:
        components.append(str(mac))

    raw = "|".join(components)
    return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()
```

> **?±ç?èªªæ?**ï¼šè¨­?™æ?ç´‹å??²å??¶é?æ¹Šå€¼ï?ä¸å??«å¯è­˜åˆ¥?‹äººèº«ä»½?„è?è¨Šã€‚AI Hub ?¶åˆ°?„æ˜¯ä¸å¯?†ç? SHA256 ?˜è???

---

## ?²è?è£½æ??¶èªª??

ä¸‹å?èªªæ??¶ä½¿?¨è€…å?è©¦å??Œä???License Key è¤‡è£½?°æœª?ˆæ?è¨­å??‚ï?ç³»çµ±å¦‚ä??æ?ï¼?

```mermaid
sequenceDiagram
    participant A as è¨­å? Aï¼ˆå·²ç¶å?ï¼?
    participant H as AI Hub
    participant B as è¨­å? Bï¼ˆå?è©¦å??¨ï?

    Note over A,H: License Key å·²æ–¼è¨­å? A é¦–æ¬¡?Ÿç”¨?‚ç?å®šå…¶?‡ç?

    A->>H: Heartbeatï¼ˆæ­£å¸¸é?ä½œä¸­ï¼?
    H-->>A: continue: true

    B->>H: POST /v1/activate<br/>{ license_key: ?Œä???Key,<br/>  device_fingerprint: ä¸å? }

    Note over H: æ¯”å? fingerprint<br/>?‡ç?å®šç??„ä??»å?

    H-->>B: 403 DEVICE_MISMATCH<br/>{ message: "æ­?Key å·²ç?å®šè‡³?¦ä??°è¨­?? }

    Note over B: å®¹å™¨ exit 1<br/>æ­?License Key å·²ç?å®šè‡³?¦ä??°è¨­?™ã€?br/>å¦‚é??´æ?è¨­å?ï¼Œè??¯çµ¡ AI Hub è§?™¤ç¶å???
```

**?¥ä½¿?¨è€…é?è¦å?æ³•æ›´?›è¨­?™ï?**

1. ?¯çµ¡ AI Hubï¼ˆai-hub@itri.org.twï¼‰ç”³è«‹è§£?¤å?è¨­å?ç¶å?
2. å¹³å°ç¢ºè?å¾Œæ??¤è©² License Key ??fingerprint ç´€??
3. ?¨æ–°è¨­å??æ–°?·è? `docker run`ï¼Œé?æ¬¡å??¨è‡ª?•å??æ–°è¨­å?ç¶å?

---

## AI Hub å¹³å°??API è¦æ ¼ï¼ˆPlatform Referenceï¼?

ä»¥ä???AI Hub ?€å¯¦ä??„ç«¯é»è??¼ï?ä¾›å¹³?°é??¼å??Šå??ƒã€?

### `POST /v1/activate`

**Request:**
```json
{
  "license_key": "lic-xxxxxxxxxxxxxxxx",
  "device_fingerprint": "sha256:abcdef...",
  "model_id": "gemma4-4b-gpu",
  "container_image": "model-cards.azurecr.io/amd/rocm/gemma4-4b@sha256:def456"
}
```

**Response 200:**
```json
{
  "session_token": "st-yyyyyyyyyy",
  "quota_tokens_remaining": 500000,
  "heartbeat_interval_seconds": 300,
  "grace_period_seconds": 1800,
  "expires_at": "2026-07-15T00:00:00Z"
}
```

**Response 4xx:**
```json
{
  "error": "DEVICE_MISMATCH",
  "message": "æ­?License Key å·²ç?å®šè‡³?¦ä??°è¨­?™ã€‚å??€?´æ?è¨­å?ï¼Œè??¯çµ¡ AI Hub è§?™¤ç¶å???
}
```

---

### `POST /v1/heartbeat`

**Request:**
```json
{
  "session_token": "st-yyyyyyyyyy",
  "device_fingerprint": "sha256:abcdef...",
  "usage_since_last_heartbeat": {
    "input_tokens": 1240,
    "output_tokens": 3871,
    "request_count": 12
  }
}
```

**Response 200:**
```json
{
  "continue": true,
  "quota_tokens_remaining": 495000,
  "next_heartbeat_seconds": 300
}
```

**Response 401ï¼ˆsession è¢«æ’¤?·æ?ï¼?**
```json
{
  "continue": false,
  "error": "SESSION_REVOKED",
  "message": "License Key å·²è¢«?¤éŠ·?–è¨­?™æ?æ¬Šå·²è§?™¤ï¼Œè??æ–°?Ÿç”¨?–è¯çµ?AI Hub??
}
```

---

## ?„é?ï¼šå®¹?¨å´å¯¦ä?è²¬ä»»?†å·¥

| ?ƒä»¶ | è² è²¬?„äº¤?¡è???|
|------|--------------|
| `entrypoint.sh` | Phase 1 ?Ÿå??Ÿç”¨?å??¨å¤±?—æ? exit 1 |
| `api.py`ï¼ˆè???taskï¼?| Phase 2 å®šæ? Heartbeat?é›¢ç·šæš«å­?|
| `api.py`ï¼ˆè?æ±‚æ??ªï?| Phase 3 ?è?æ±‚é?é¡é˜²è­·ï?429 ?æ?ï¼?|
| `ryzenai/modules/` | **ä¸æ??Šä»»ä½•äº¤?¡é?è¼?*ï¼ˆç”±æ¡†æ¶å±¤çµ±ä¸€?•ç?ï¼?|
