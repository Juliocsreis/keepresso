# -*- coding: utf-8 -*-
"""Offline pause: let a lid-closed Mac sleep when it has no internet."""

CORE = {
    "Not started, no internet with the lid closed": {
        "hu": "Nem indult el, nincs internet csukott fedélnél", "es": "No iniciado, sin internet con la tapa cerrada", "fr": "Non démarré, pas d’internet capot fermé", "de": "Nicht gestartet, kein Internet bei geschlossenem Deckel", "zh-Hans": "未启动，合盖时没有网络",
        "it": "Non avviato, nessuna connessione internet con il coperchio chiuso", "ja": "未開始、蓋が閉じた状態でインターネットに接続できません", "ko": "시작되지 않음, 덮개가 닫힌 상태에서 인터넷 연결 없음", "ru": "Не запущено, нет интернета при закрытой крышке", "pt-BR": "Não iniciado, sem internet com a tampa fechada", "tr": "Başlatılmadı, kapak kapalıyken internet yok", "pl": "Nie uruchomiono, brak internetu przy zamkniętej pokrywie", "uk": "Не запущено, немає інтернету із закритою кришкою", "zh-Hant": "未啟動，闔蓋時沒有網路",
    },
    "Paused, no internet with the lid closed": {
        "hu": "Szüneteltetve, nincs internet csukott fedélnél", "es": "En pausa, sin internet con la tapa cerrada", "fr": "En pause, pas d’internet capot fermé", "de": "Pausiert, kein Internet bei geschlossenem Deckel", "zh-Hans": "已暂停，合盖时没有网络",
        "it": "In pausa, nessuna connessione internet con il coperchio chiuso", "ja": "一時停止、蓋が閉じた状態でインターネットに接続できません", "ko": "일시 정지됨, 덮개가 닫힌 상태에서 인터넷 연결 없음", "ru": "Приостановлено, нет интернета при закрытой крышке", "pt-BR": "Pausado, sem internet com a tampa fechada", "tr": "Duraklatıldı, kapak kapalıyken internet yok", "pl": "Wstrzymano, brak internetu przy zamkniętej pokrywie", "uk": "Призупинено, немає інтернету із закритою кришкою", "zh-Hant": "已暫停，闔蓋時沒有網路",
    },
    "Paused, no internet": {
        "hu": "Szüneteltetve, nincs internet", "es": "En pausa, sin internet", "fr": "En pause : pas d’internet", "de": "Pausiert, kein Internet", "zh-Hans": "已暂停，没有网络",
        "it": "In pausa, nessuna connessione internet", "ja": "インターネットなしで一時停止", "ko": "인터넷 연결 없음으로 일시 정지됨", "ru": "Приостановлено, нет интернета", "pt-BR": "Pausado, sem internet", "tr": "Duraklatıldı, internet yok", "pl": "Wstrzymano, brak internetu", "uk": "Призупинено, немає інтернету", "zh-Hant": "已暫停，沒有網路",
    },
    "The lid is closed and the Mac has been offline too long, so Keepresso is letting it sleep. Opening the lid resumes the session.": {
        "hu": "A fedél csukva van, és a Mac túl régóta offline, ezért a Keepresso hagyja elaludni. A fedél felnyitásával a munkamenet folytatódik.",
        "es": "La tapa está cerrada y el Mac lleva demasiado tiempo sin conexión, así que Keepresso lo deja en reposo. Al abrir la tapa, la sesión se reanuda.",
        "fr": "Le capot est fermé et le Mac est hors ligne depuis trop longtemps, Keepresso le laisse donc se mettre en veille. Ouvrir le capot reprend la session.",
        "de": "Der Deckel ist geschlossen und der Mac ist zu lange offline, daher lässt Keepresso ihn ruhen. Wenn du den Deckel öffnest, wird die Sitzung fortgesetzt.",
        "zh-Hans": "已合盖且 Mac 离线时间过长，因此 Keepresso 让它进入睡眠。打开盖子即可恢复会话。",
        "it": "Il coperchio è chiuso e il Mac è offline da troppo tempo, quindi Keepresso lo lascia andare in stop. Aprendo il coperchio la sessione riprende.",
        "ja": "蓋が閉じた状態で Mac が長時間オフラインのため、Keepresso はスリープを許可しています。蓋を開けるとセッションが再開します。",
        "ko": "덮개가 닫혀 있고 Mac이 너무 오래 오프라인 상태여서 Keepresso가 잠자기를 허용합니다. 덮개를 열면 세션이 재개됩니다.",
        "ru": "Крышка закрыта, а Mac слишком долго без интернета, поэтому Keepresso позволяет ему уйти в сон. Если открыть крышку, сеанс возобновится.",
        "pt-BR": "A tampa está fechada e o Mac está sem internet há tempo demais, então o Keepresso está deixando ele repousar. Abrir a tampa retoma a sessão.",
        "tr": "Kapak kapalı ve Mac çok uzun süredir çevrimdışı, bu yüzden Keepresso uyumasına izin veriyor. Kapağı açmak oturumu sürdürür.",
        "pl": "Pokrywa jest zamknięta, a Mac jest zbyt długo offline, więc Keepresso pozwala mu przejść w stan uśpienia. Otwarcie pokrywy wznowi sesję.",
        "uk": "Кришка закрита, а Mac надто довго без інтернету, тому Keepresso дозволяє йому заснути. Якщо відкрити кришку, сеанс поновиться.",
        "zh-Hant": "已闔蓋且 Mac 離線時間過長，因此 Keepresso 讓它進入睡眠。打開上蓋即可恢復工作階段。",
    },
    "Resumed, internet or lid back": {
        "hu": "Folytatva, visszajött az internet vagy felnyílt a fedél", "es": "Reanudado, volvió internet o se abrió la tapa", "fr": "Reprise, internet rétabli ou capot ouvert", "de": "Fortgesetzt, Internet zurück oder Deckel geöffnet", "zh-Hans": "已恢复，网络已恢复或已打开盖子",
        "it": "Ripreso, internet tornato o coperchio aperto", "ja": "再開、インターネット回復または蓋が開かれました", "ko": "재개됨, 인터넷 복구 또는 덮개 열림", "ru": "Возобновлено, интернет вернулся или крышка открыта", "pt-BR": "Retomado, internet de volta ou tampa aberta", "tr": "Devam edildi, internet geri geldi veya kapak açıldı", "pl": "Wznowiono, internet wrócił lub otwarto pokrywę", "uk": "Поновлено, інтернет повернувся або кришку відкрито", "zh-Hant": "已恢復，網路已恢復或已打開上蓋",
    },
    "Offline pause": {
        "hu": "Offline szünet", "es": "Pausa sin conexión", "fr": "Pause hors ligne", "de": "Offline-Pause", "zh-Hans": "离线暂停",
        "it": "Pausa offline", "ja": "オフライン一時停止", "ko": "오프라인 일시 정지", "ru": "Пауза без интернета", "pt-BR": "Pausa sem internet", "tr": "Çevrimdışı duraklatma", "pl": "Pauza offline", "uk": "Пауза без інтернету", "zh-Hant": "離線暫停",
    },
}

APP = {
    "Keepresso paused with no internet but can't switch off closed-display mode without the administrator helper (Preferences ▸ General).": {
        "hu": "A Keepresso szüneteltetve lett internet hiányában, de a rendszergazdai segéd nélkül nem tudja kikapcsolni a csukott fedél módot (Beállítások ▸ Általános).",
        "es": "Keepresso se pausó por falta de internet pero no puede desactivar el modo con pantalla cerrada sin el asistente de administrador (Ajustes ▸ General).",
        "fr": "Keepresso s’est mis en pause faute d’internet, mais ne peut pas désactiver le mode écran fermé sans l’assistant administrateur (Réglages ▸ Général).",
        "de": "Keepresso hat ohne Internet pausiert, kann aber ohne den Administrator-Hilfsdienst (Einstellungen ▸ Allgemein) den Modus bei geschlossenem Display nicht ausschalten.",
        "zh-Hans": "Keepresso 已因没有网络暂停，但没有管理员助理（偏好设置 ▸ 通用）就无法关闭合盖模式。",
        "it": "Keepresso si è messo in pausa per mancanza di internet ma non può disattivare la modalità a schermo chiuso senza l’assistente amministratore (Impostazioni ▸ Generali).",
        "ja": "Keepresso はインターネットがないため一時停止しましたが、管理者ヘルパーがないとクラムシェルモードをオフにできません（設定 ▸ 一般）。",
        "ko": "Keepresso가 인터넷 연결이 없어 일시 정지되었지만, 관리자 도우미 없이는 디스플레이 닫힘 모드를 끌 수 없습니다 (환경설정 ▸ 일반).",
        "ru": "Keepresso поставил сеанс на паузу из-за отсутствия интернета, но не может отключить режим закрытой крышки без помощника с правами администратора (Настройки ▸ Общие).",
        "pt-BR": "O Keepresso pausou por falta de internet, mas não pode desativar o modo com tela fechada sem o assistente de administrador (Preferências ▸ Geral).",
        "tr": "Keepresso internet olmadığı için duraklatıldı ancak yönetici yardımcısı olmadan kapalı ekran modunu kapatamıyor (Tercihler ▸ Genel).",
        "pl": "Keepresso wstrzymało sesję z powodu braku internetu, ale nie może wyłączyć trybu zamkniętej pokrywy bez pomocnika administratora (Ustawienia ▸ Ogólne).",
        "uk": "Keepresso призупинив сеанс через відсутність інтернету, але не може вимкнути режим закритої кришки без помічника із правами адміністратора (Налаштування ▸ Загальні).",
        "zh-Hant": "Keepresso 已因沒有網路而暫停，但若無系統管理員輔助程式（偏好設定 ▸ 一般），便無法關閉闔蓋模式。",
    },
    "No internet with the lid closed, letting the Mac sleep": {
        "hu": "Nincs internet csukott fedélnél, a Mac elalhat", "es": "Sin internet con la tapa cerrada, dejando que el Mac repose", "fr": "Pas d’internet capot fermé, le Mac peut se mettre en veille", "de": "Kein Internet bei geschlossenem Deckel, Mac darf ruhen", "zh-Hans": "合盖时没有网络，正在让 Mac 睡眠",
        "it": "Nessuna connessione internet con il coperchio chiuso, il Mac può andare in stop", "ja": "蓋が閉じた状態でインターネットがないため、Mac をスリープさせます", "ko": "덮개가 닫힌 상태에서 인터넷 연결이 없어 Mac이 잠자도록 함", "ru": "Нет интернета при закрытой крышке, Mac может уйти в сон", "pt-BR": "Sem internet com a tampa fechada, deixando o Mac repousar", "tr": "Kapak kapalıyken internet yok, Mac'in uyumasına izin veriliyor", "pl": "Brak internetu przy zamkniętej pokrywie, Mac może przejść w stan uśpienia", "uk": "Немає інтернету із закритою кришкою, Mac може заснути", "zh-Hant": "闔蓋時沒有網路，讓 Mac 睡眠",
    },
    "Let the Mac sleep when offline with the lid closed": {
        "hu": "A Mac elalhat, ha csukott fedélnél nincs internet", "es": "Dejar que el Mac repose sin internet con la tapa cerrada", "fr": "Laisser le Mac se mettre en veille hors ligne, capot fermé", "de": "Mac ruhen lassen, wenn er bei geschlossenem Deckel offline ist", "zh-Hans": "合盖时离线则让 Mac 睡眠",
        "it": "Lascia andare il Mac in stop se è offline con il coperchio chiuso", "ja": "蓋を閉じた状態でオフラインなら Mac をスリープさせる", "ko": "덮개를 닫은 상태에서 오프라인이면 Mac 잠자기 허용", "ru": "Разрешать Mac уходить в сон без интернета при закрытой крышке", "pt-BR": "Deixar o Mac repousar sem internet com a tampa fechada", "tr": "Kapak kapalıyken çevrimdışı olunca Mac'in uyumasına izin ver", "pl": "Pozwól Macowi przejść w stan uśpienia, gdy jest offline przy zamkniętej pokrywie", "uk": "Дозволяти Mac засинати без інтернету із закритою кришкою", "zh-Hant": "闔蓋時離線就讓 Mac 睡眠",
    },
    "With the lid closed and closed-display mode active, Keepresso checks the internet every 20 seconds. If it stays unreachable for this long, the session pauses and the Mac can sleep. When the Mac has no network at all, hotspot fallback (if set up) gets a try first. Opening the lid resumes the session.": {
        "hu": "Csukott fedélnél, bekapcsolt csukott fedél móddal a Keepresso 20 másodpercenként ellenőrzi az internetet. Ha ennyi ideig elérhetetlen marad, a munkamenet szünetel, és a Mac elalhat. Ha a Macnek egyáltalán nincs hálózata, előbb a beállított hotspot-tartalékot próbálja. A fedél felnyitásával a munkamenet folytatódik.",
        "es": "Con la tapa cerrada y el modo con pantalla cerrada activo, Keepresso comprueba internet cada 20 segundos. Si sigue sin conexión durante este tiempo, la sesión se pausa y el Mac puede reposar. Si el Mac no tiene ninguna red, primero se intenta el punto de acceso de respaldo (si está configurado). Al abrir la tapa, la sesión se reanuda.",
        "fr": "Capot fermé et mode écran fermé actif, Keepresso vérifie internet toutes les 20 secondes. S’il reste inaccessible pendant cette durée, la session se met en pause et le Mac peut se mettre en veille. Si le Mac n’a aucun réseau, le partage de connexion de secours (s’il est configuré) est essayé d’abord. Ouvrir le capot reprend la session.",
        "de": "Bei geschlossenem Deckel und aktivem Modus bei geschlossenem Display prüft Keepresso alle 20 Sekunden das Internet. Bleibt es so lange unerreichbar, pausiert die Sitzung und der Mac darf ruhen. Hat der Mac gar kein Netzwerk, wird zuerst ein eingerichteter Hotspot als Ersatzverbindung versucht. Wenn du den Deckel öffnest, wird die Sitzung fortgesetzt.",
        "zh-Hans": "合盖且合盖模式开启时，Keepresso 每 20 秒检查一次网络。如果在这段时间内一直无法连接，会话会暂停，Mac 可以睡眠。如果 Mac 完全没有网络，会先尝试连接备用热点（如已设置）。打开盖子即可恢复会话。",
        "it": "Con il coperchio chiuso e la modalità a schermo chiuso attiva, Keepresso controlla internet ogni 20 secondi. Se resta irraggiungibile per questo tempo, la sessione va in pausa e il Mac può andare in stop. Se il Mac non ha alcuna rete, viene provato prima l’hotspot di riserva (se configurato). Aprendo il coperchio la sessione riprende.",
        "ja": "蓋が閉じていてクラムシェルモードがオンのとき、Keepresso は 20 秒ごとにインターネットを確認します。この時間ずっと接続できなければ、セッションを一時停止して Mac をスリープさせます。Mac がまったくネットワークに接続していない場合は、先に予備のホットスポット（設定済みの場合）を試します。蓋を開けるとセッションが再開します。",
        "ko": "덮개가 닫혀 있고 디스플레이 닫힘 모드가 켜져 있으면 Keepresso가 20초마다 인터넷을 확인합니다. 이 시간 동안 계속 연결되지 않으면 세션이 일시 정지되고 Mac이 잠자기에 들어갈 수 있습니다. Mac에 네트워크가 전혀 없으면 예비 핫스팟(설정한 경우)을 먼저 시도합니다. 덮개를 열면 세션이 재개됩니다.",
        "ru": "При закрытой крышке и включённом режиме закрытой крышки Keepresso проверяет интернет каждые 20 секунд. Если он недоступен всё это время, сеанс ставится на паузу и Mac может уйти в сон. Если у Mac вообще нет сети, сначала пробуется резервная точка доступа (если она настроена). Если открыть крышку, сеанс возобновится.",
        "pt-BR": "Com a tampa fechada e o modo com tela fechada ativo, o Keepresso verifica a internet a cada 20 segundos. Se ela continuar inacessível por esse tempo, a sessão pausa e o Mac pode repousar. Quando o Mac não tem nenhuma rede, o hotspot de reserva (se configurado) é tentado primeiro. Abrir a tampa retoma a sessão.",
        "tr": "Kapak kapalı ve kapalı ekran modu açıkken Keepresso interneti 20 saniyede bir kontrol eder. Bu süre boyunca erişilemezse oturum duraklar ve Mac uyuyabilir. Mac'in hiç ağı yoksa, ayarlanmışsa önce yedek erişim noktası denenir. Kapağı açmak oturumu sürdürür.",
        "pl": "Przy zamkniętej pokrywie i włączonym trybie zamkniętej pokrywy Keepresso sprawdza internet co 20 sekund. Jeśli przez ten czas pozostaje niedostępny, sesja zostaje wstrzymana, a Mac może przejść w stan uśpienia. Gdy Mac nie ma żadnej sieci, najpierw próbowany jest hotspot zapasowy (jeśli jest skonfigurowany). Otwarcie pokrywy wznowi sesję.",
        "uk": "Із закритою кришкою та ввімкненим режимом закритої кришки Keepresso перевіряє інтернет кожні 20 секунд. Якщо весь цей час він недоступний, сеанс призупиняється, і Mac може заснути. Якщо в Mac взагалі немає мережі, спершу пробується резервна точка доступу (якщо її налаштовано). Якщо відкрити кришку, сеанс поновиться.",
        "zh-Hant": "闔蓋且闔蓋模式開啟時，Keepresso 每 20 秒檢查一次網路。若在這段時間內一直無法連線，工作階段會暫停，Mac 可以睡眠。若 Mac 完全沒有網路，會先嘗試連線備用熱點（若已設定）。打開上蓋即可恢復工作階段。",
    },
}
