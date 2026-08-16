# Рабочая машина: VDS + dedicated ISP AS9198

Один контур. Квартиры в Казахстане нет. Ноутбук не держим включённым.

- **Считать** — VDS 24/7: Claude Code, git, IDE (Remote-SSH или code-server).
- **Выходить в интернет** — dedicated IPv4 **AS9198**.
- **Заходить из РФ** — SSH на IPv4 хостера (Москва/СПб).
- **SMS** — eSIM на ваш ИИН (`8 7xx`).
- **Локаль VDS** — `Asia/Almaty`, `ru_KZ` / `kk_KZ`.

Не путать: VPS «в Казахстане» (PS.kz и т.п.) даёт **хостинг-ASN**, не AS9198 абонентского Казахтелекома. IP карточки VDS сайты видеть не должны.

Документ — для работы с сервисами на свои документы. Чужой ИИН, обход KYC, мультиаккаунтинг — вне scope.

---

## 1. Как это устроено

Сайты смотрят на исходящий IP процесса **на VDS**. Этот процесс не должен ходить в интернет с `eth0` хостера. Весь TCP/UDP (и DNS) уходит в SOCKS5 dedicated ISP. Шлюз прокси — обычный датацентр; **exit IP** после шлюза — префикс Казахтелекома.

```mermaid
flowchart LR
  YOU["Ноутбук в РФ<br/>VS Code Remote-SSH"] -->|TCP 22<br/>на IPv4 хостера| VDS
  subgraph vds ["VDS 24/7"]
    APP["claude, git, code-server"]
    TUN["sing-box TUN"]
    APP --> TUN
  end
  TUN -->|"SOCKS5, один порт = один IP<br/>без ротации"| GW["Шлюз поставщика<br/>disp.oxylabs.io и т.п."]
  GW --> EXIT["EXIT_IP<br/>BGP origin AS9198"]
  EXIT --> WEB["Сайты видят Казахтелеком"]
  PH["Телефон, eSIM на ИИН"] -.->|SMS 8 7xx| WEB
```

На пакете:

1. Приложение на VDS шлёт в `tun0`.
2. sing-box (или tun2socks) открывает SOCKS5 к `host:port` из кабинета. Этот `host` — **не** казахский IP.
3. Поставщик подставляет **ваш** dedicated IPv4. В RIPEstat origin AS = **9198**, holder Kazakhtelecom.
4. SSH/RDP идут в обход TUN, иначе при падении прокси вы потеряете сервер.

Ограничения (это не квартира на GPON):

- Адрес арендован у ISP и крутится на стойке поставщика. ASN — Казахтелеком; тип «домашний роутер» базы могут всё равно пометить как proxy.
- Dedicated = этот IPv4 только у вас на срок подписки. Shared/rotating не подходит.
- Город в GeoIP может быть грубым (Алматы vs Астана) — выровняйте профили под то, что показывает RIPEstat/ipinfo.

---

## 2. Что покупать (и что не покупать)

| Нужно | Не нужно |
| --- | --- |
| 1× **dedicated static ISP**, страна **KZ**, ASN **AS9198** | Residential rotating, mobile pool, VPN «Kazakhstan» |
| SOCKS5 (удобнее для TUN) или HTTPS | Порт ротации (у Oxylabs это `:8000`) |
| VDS: Ubuntu 24.04, **4 vCPU / 8 GB / NVMe**, IPv4, ЦОД РФ для SSH | VDS как *исходящий* IP; Windows Server «для всего»; 1–2 GB RAM |
| Проверка RIPEstat **до** привязки аккаунтов | «миллионы KZ residential» без whois |

AS9198: [IPinfo](https://ipinfo.io/AS9198), [PeeringDB](https://www.peeringdb.com/asn/9198) (карточка обновлялась **05.08.2026**).

Не засчитывать exit: AS210976 Timeweb, AS200590 NLS, **AS48716 PS Internet**, AS29355 Kcell (мобильный), «KZ» у VPN.

Поставщики, у которых *вообще бывает* dedicated ISP (слот **KZ+9198** смотреть в кабинете, не в рекламе):

| Продукт | ASN AS9198 до оплаты | Статический dedicated | Документация |
| --- | --- | --- | --- |
| **Oxylabs Dedicated ISP** | Выбор premium ASN при Buy Now; если ASN пустой — случайный | Да, порт = один IP | [Start using DISP](https://developers.oxylabs.io/help-center/getting-started/start-using-dedicated-isp-proxies) |
| **IPRoyal ISP** | Только поле Extra Requirements: `ASN AS9198` | Да, на весь срок подписки | [ISP Quick-Start, Q2 2026](https://iproyal.com/quick-start-guides/static-residential-proxies/) |
| **Bright Data ISP dedicated** | **Нельзя.** Только страна `kz`; ASN проверяете после выдачи | Да, unlimited per IP | [Configure ISP](https://docs.brightdata.com/proxy-networks/isp/configure-your-proxy) |

У Oxylabs в маркетинге ASN — Comcast/Verizon/Orange. Казахтелеком там может **не быть**. Bright Data: `-asn-` есть только у **Residential**, не у ISP ([geo targeting](https://docs.brightdata.com/api-reference/proxy/geolocation-targeting), [config-options](https://docs.brightdata.com/proxy-networks/config-options)).

SOAX `asn-9198` и Bright Data Residential `-asn-9198` — **не** dedicated: IP не ваш на месяц. Не использовать в этом контуре.

---

## 3. Шаг за шагом

### 3.1. Письмо поставщику до оплаты

> Need **1 dedicated static ISP IPv4**, country **KZ**, **private** (not shared, not rotating).  
> BGP origin must be **AS9198** (JSC Kazakhtelecom).  
> Send **exit IP** before charge, or 24h trial + free replace if RIPEstat `network-info` is not AS9198.  
> SOCKS5. No rotation.

Нет IP/whois заранее и нет trial — не брать пачку.

### 3.2. Заказ 1 IP

**Oxylabs** ([страны только в dashboard](https://developers.oxylabs.io/help-center/products-and-features/what-countries-do-oxylabs-proxies-cover), [ASN/RIPEstat](https://developers.oxylabs.io/products/proxies/dedicated-isp-proxies/self-service/location-settings)):

1. [dashboard.oxylabs.io](https://dashboard.oxylabs.io/en/) → Dedicated ISP → Buy Now.
2. Нет **Kazakhstan** — стоп.
3. ASN: Kazakhtelecom / **9198**. Не оставлять пустым.
4. 1 IP, создать user. Список: My Products → Proxy List (entry, **port**, country, ASN, assigned IP).
5. Для фиксации IP — порт вроде `8001`, **не** `8000` (ротация по вашему списку).

```bash
curl -x socks5h://user-USERNAME:PASSWORD@disp.oxylabs.io:8001 https://ip.oxylabs.io/location
```

**IPRoyal** ([Q2 2026](https://iproyal.com/quick-start-guides/static-residential-proxies/)):

1. ISP → Create order → location Kazakhstan, **1** IP, минимальный срок.
2. Extra Requirements: `ASN AS9198 Kazakhtelecom, dedicated, not hosting`.
3. Protocol SOCKS5, порт по умолчанию `12324`. Прогнать встроенный Proxy Tester.

**Bright Data ISP dedicated** ([configure](https://docs.brightdata.com/proxy-networks/isp/configure-your-proxy)):

1. Zone ISP → dedicated + unlimited, country **только `kz`**.
2. Download allocated IPs. Сразу §3.3. Не 9198 — refresh/отказ, не оставлять.

ISP ≠ домашний Wi‑Fi: [IPRoyal FAQ, 27.02.2026](https://help.iproyal.com/en/articles/7222102-are-the-proxies-from-real-residential-ip-addresses).

### 3.3. Приёмка ASN (RIPEstat, не MaxMind)

Oxylabs: коммерческие базы часто показывают регистрационного владельца, не текущий BGP. Источник: [RIPEstat](https://stat.ripe.net/), [Network Info](https://stat.ripe.net/docs/data-api/api-endpoints/network-info), [Prefix Overview](https://stat.ripe.net/docs/data-api/api-endpoints/prefix-overview).

`EXIT_IP` — адрес из кабинета / из `ipify` **через прокси**, не `disp.oxylabs.io`.

```bash
curl -sS "https://stat.ripe.net/data/network-info/data.json?resource=EXIT_IP"
curl -sS "https://stat.ripe.net/data/prefix-overview/data.json?resource=EXIT_IP"
curl -sS "https://stat.ripe.net/data/as-overview/data.json?resource=AS9198"
```

UI: `https://stat.ripe.net/EXIT_IP`

Критерий:

1. `asns` содержит **только / в том числе 9198**.
2. Holder — JSC Kazakhtelecom.
3. Geo — **KZ**.
4. Тот же `host:port` через 15 минут → **тот же** EXIT_IP.
5. IP2Location usage не `DCH` хостинга (Timeweb/PS). Флаг `proxy` у ISP-прокси бывает — критичен чужой **hosting ASN**.

Дополнительно: [ipinfo.io/EXIT_IP](https://ipinfo.io), [bgp.he.net/ip/EXIT_IP](https://bgp.he.net).

Не прошло — замена у поставщика, не «потом привыкнет».

### 3.4. VDS, на который спокойно заходят из РФ

IP этого сервера **не** должен светиться сайтам (см. TUN). Он нужен только чтобы **вы из России** открыли SSH/RDP и чтобы машина жила 24/7. Поэтому датацентр в Москве/СПб часто удобнее Франкфурта: пинг до консоли ниже, оплату не режут санкционные шлюзы.

Что проверить до оплаты: панель открывается без VPN, SSH с вашего домашнего провайдера РФ (`Test-NetConnection IP -Port 22` / `nc -vz IP 22`), есть **VNC/консоль** в кабинете на случай блокировки 22, IPv4 включён, СБП/МИР/ЮMoney видны на шаге оплаты.

#### Не начинать с этого (оплата/аккаунт из РФ)

Hetzner, DigitalOcean, AWS, Vultr, OVH, Contabo — в 2026 карты российских банков на их шлюзах, как правило, **не проходят**; доступ к панели бывает, биллинг — нет. Обзоры: [оплата DigitalOcean из РФ, 2026](https://vc.ru/services/2684194-oplata-digitalocean-v-rossii), [Hetzner из РФ](https://dtf.ru/howto/3920357-oplata-hetzner-v-rossii). Посредники и «иностранные карты» — отдельный риск блокировки аккаунта, для этого контура не нужно.

#### Рабочие варианты (рубли, русская панель, SSH из РФ)

Сводка обзоров **2026**: [зарубежный VPS с оплатой из России](https://vc.ru/toprate/2935681-zarubezhnyy-vps-s-oplatoy-iz-rossii), [VPS с картой «Мир», май 2026](https://dtf.ru/top-raiting/4767988-luchshie-vps-vds-s-oplate-mir), [VPS без KYC, август 2026](https://vc.ru/top-raiting/2879899-luchshie-vps-vds-bez-kyc), [рубли без серых схем](https://tproger.ru/articles/10-zarubezhnyh-vps--gde-mozhno-platit-v-rublyah---bez-seryh-shem), [VDS для сайта, август 2026](https://vc.ru/top-raiting/2314696-luchshie-vds-vps-dlya-arendy-servera-dlya-sayta). Тарифы и способы оплаты сверяйте в кабинете — они меняются.

| Хостер | Зачем в этом контуре | Локации (заявленные) | Оплата из РФ | Сайт |
| --- | --- | --- | --- | --- |
| **Timeweb Cloud** | Почасовой биллинг, можно проверить SSH за час. Есть **Алматы** — это всё равно **хостинг**, не AS9198 exit | Москва, СПб, Новосибирск, Казахстан, Польша, Нидерланды | Карты, облако под РФ | [timeweb.cloud VPS Linux](https://timeweb.cloud/services/vps-linux) |
| **Aeza** | Мощное железо, Anti-DDoS, низкий пинг из РФ на локациях РФ | РФ + зарубежные (см. кабинет) | МИР, СБП, ЮMoney, крипта | [aeza.net](https://aeza.net/) / [aeza.ru](https://aeza.ru) |
| **VDSina** | Простой KVM/NVMe, быстрый заказ | В основном РФ | Рубли, карты | [vdsina.ru](https://vdsina.ru) |
| **AdminVPS** | Европа + русская поддержка; в обзорах 2026 — DE/NL/FI и **Казахстан** | РФ, Европа, KZ | Привычные РФ-методы | [adminvps.ru](https://adminvps.ru) |
| **Fornex** | Нормальный европейский VPS без квеста с Hetzner | DE, NL, SE, CH, ES, US, РФ | МИР, СБП, карты (проверять в кассе) | [fornex.com](https://fornex.com) |
| **JustHost** | Много стран, удобно снять минималку и прогнать пинг/SSH | Десятки ДЦ | Карты РФ, СБП и др. | [justhost.ru](https://justhost.ru) |
| **Hostiman** | Простой вход, поддержка на русском | Зарубежные + РФ | Оплата из России | [hostiman.com](https://hostiman.com) / [hostiman.ru](https://hostiman.ru) |
| **FirstVDS** | KVM, Москва и **Нидерланды** | РФ, NL | Рубли | [firstvds.ru](https://firstvds.ru) |
| **Beget** | Стабильный массовый хостинг, Windows/Linux VPS | РФ | МИР/СБП | [beget.com](https://beget.com) |
| **ISHosting** | Много стран, если нужен EU IP на карточке VDS (на exit не влияет) | 40+ стран | СБП, ЮMoney, крипта | [ishosting.com](https://ishosting.com) |

Для **подключения из РФ** разумный порядок:

1. Сначала **Timeweb Cloud / Aeza / VDSina / Beget** в **Москве или СПб**: SSH почти всегда проходит у Ростелекома, МТС, ТТК, домашних GPON.
2. Если нужен EU-адрес у самого VDS (не для сайтов, а чтобы хостер не был «RU hosting» в whois карточки) — **Fornex NL/DE**, **AdminVPS NL/FI**, **Timeweb Amsterdam**, **FirstVDS NL**. С дома в РФ SSH туда обычно жив; если 22 режут — сразу консоль в панели и перенос SSH на `443`/`2222`.
3. Локация **Алматы у Timeweb/AdminVPS** не заменяет dedicated AS9198. Это ближе по пингу к прокси-шлюзу в Азии, но RIPEstat хостера ≠ 9198.

### 3.4.1. Конфигурация VDS под Claude Code и IDE

Нагрузка, под которую считаем тариф: **sing-box TUN + Claude Code CLI + VS Code Remote-SSH** (vscode-server на VDS). GUI-рабочий стол и JetBrains — не дефолт.

| Профиль | vCPU | RAM | Диск | Для чего |
| --- | --- | --- | --- | --- |
| Минимум | 2 | **4 GB** | 40 GB NVMe | Только `tmux` + `claude`, мелкий репозиторий. OOM на длинной сессии реален |
| **Брать это** | **4** | **8 GB** | **80–120 GB NVMe** | Claude Code + Remote-SSH + расширения + `npm`/`pip` + git |
| С запасом | 4–8 | 16 GB | 160 GB+ | code-server в браузере, Docker, два агента сразу |
| Не как база | 8+ | 16 GB+ | 200 GB+ | JetBrains Gateway / полный xrdp — дорого и не нужно для Claude Code |

Ориентиры: официальный пол Claude Code — **4 GB RAM** ([setup](https://code.claude.com/docs/en/setup.md)); связка code-server + Claude — пол 4 GB, комфорт 8 GB / 4 vCPU ([обзор стека](https://cloudzy.com/blog/code-server-claude-code-vps/)). vscode-server Remote-SSH ест RAM сам по себе; 2 GB на этот контур не закладывать.

**ОС и виртуализация**

- **Ubuntu 24.04 LTS x64**, KVM (не OpenVZ/виртуальный «VPS без TUN»: нужен `/dev/net/tun` для sing-box).
- Не Windows Server: RDP из РФ режут, RAM на GUI, Claude Code на Linux проще.
- Не «только IPv6».
- 1–2 GB **swap** как предохранитель OOM, не вместо 8 GB RAM.

**Сеть и порты (вход с РФ = IP хостера, не 9198)**

| Порт | Куда | В TUN `direct`? |
| --- | --- | --- |
| **22** или **2222** SSH | Обязательно, ключи, без пароля root | Да, как сейчас для 22 |
| **8080/8443** code-server | Лучше **не** в интернет: `ssh -L 8080:127.0.0.1:8080`. Если открываете наружу — ufw + пароль/TLS | Слушать `127.0.0.1` |
| 3389 RDP | Не использовать | — |
| ICMP/панель VNC | Консоль хостера, не порт в ufw | — |

UFW: `allow 22/tcp` (или 2222), `default deny incoming`, `allow outgoing`. Исходящий к Anthropic и git идёт уже через TUN.

**Где заказать (под эту спецификацию)**

1. ЦОД **Москва или СПб**, хостер из таблицы выше (Timeweb Cloud почасовка — удобно проверить SSH).
2. В конфигураторе: 4 vCPU, 8 GB, диск ≥ 80 GB NVMe, **IPv4**, Ubuntu 24.04, KVM.
3. После выдачи: в панели есть VNC; `ssh -i key user@VDS_IP` с домашнего РФ **до** установки TUN.

**Пакеты на VDS** (после первого `apt update && apt upgrade`):

```bash
sudo apt install -y git tmux curl ca-certificates ufw fail2ban \
  build-essential python3-venv unzip
# TUN
# sing-box — по §3.6
# Claude Code
curl -fsSL https://claude.ai/install.sh | bash
```

Не ставить GNOME/KDE. Браузер на сервере не обязателен: VS Code сидит на ноутбуке (Remote-SSH), API Claude — с VDS.

Пользователь не-root, SSH только по ключу, `PermitRootLogin no`. Сессии Claude — в `tmux`.

Запасной доступ: VNC/KVM в панели **до** включения TUN. Иначе при кривом sing-box потеряете SSH.

### 3.5. Локаль на VDS

Гео карточки VDS сайты не видят, если TUN без утечек. Локаль нужна процессам на машине (даты, `LANG`).

```bash
sudo timedatectl set-timezone Asia/Almaty
sudo apt install -y locales
sudo sed -i 's/^# *ru_KZ.UTF-8/ru_KZ.UTF-8/' /etc/locale.gen
sudo locale-gen
sudo update-locale LANG=ru_KZ.UTF-8
```

При необходимости добавьте `kk_KZ.UTF-8` тем же способом.

### 3.6. Прозрачный выход: sing-box TUN

`HTTP_PROXY` в cron/Chrome ненадёжен. Нужен TUN: [sing-box client](https://sing-box.sagernet.org/manual/proxy/client/), [tun inbound](https://sing-box.sagernet.org/configuration/inbound/tun/). На Linux включайте `auto_redirect`.

Подставьте host/port/user/pass из кабинета. `direct` обязателен для SSH и для IP **шлюза** прокси (иначе петля).

```json
{
  "log": { "level": "info" },
  "dns": {
    "servers": [{ "type": "udp", "server": "8.8.8.8" }],
    "strategy": "ipv4_only"
  },
  "inbounds": [
    {
      "type": "tun",
      "tag": "tun-in",
      "address": ["172.19.0.1/30"],
      "auto_route": true,
      "auto_redirect": true,
      "strict_route": true
    }
  ],
  "outbounds": [
    {
      "type": "socks",
      "tag": "isp",
      "server": "disp.oxylabs.io",
      "server_port": 8001,
      "version": "5",
      "username": "user-USERNAME",
      "password": "PASSWORD"
    },
    { "type": "direct", "tag": "direct" }
  ],
  "route": {
    "auto_detect_interface": true,
    "final": "isp",
    "rules": [
      { "port": 22, "outbound": "direct" },
      { "ip_cidr": ["<IP_ШЛЮЗА_ПРОКСИ>/32"], "outbound": "direct" }
    ]
  }
}
```

IP шлюза: `getent hosts disp.oxylabs.io` (или хост IPRoyal) — **A-запись шлюза**, не EXIT_IP.

systemd (бинарник в `/usr/local/bin/sing-box`, конфиг `/etc/sing-box/config.json`):

```ini
[Unit]
Description=sing-box TUN to dedicated ISP AS9198
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/sing-box run -c /etc/sing-box/config.json
Restart=on-failure
RestartSec=5
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now sing-box
curl -4 https://api.ipify.org
# == EXIT_IP из кабинета
curl -sS "https://stat.ripe.net/data/network-info/data.json?resource=$(curl -sS https://api.ipify.org)"
```

Альтернатива без sing-box: [tun2socks → SOCKS5](https://bigmike.help/en/devops/routing-all-system-traffic-through-a-socks5-proxy-using-tun2socks/) — TUN, маршрут default в tun0, **исключить** IP SOCKS-сервера и порт 22, systemd.

Пока TUN down — наружу (кроме SSH) не ходить: иначе cron уйдёт с IP хостера.

Проверка утечек с VDS: `curl -4 https://api.ipify.org` и RIPEstat. Браузер на сервере не нужен; если поставите Chrome — [browserleaks.com/ip](https://browserleaks.com/ip), WebRTC не должен показать IP VDS.

### 3.7. Чеклист

- [ ] Тариф VDS: **4 vCPU / 8 GB / NVMe ≥ 80 GB**, Ubuntu 24.04 KVM, IPv4, ЦОД РФ (§3.4.1).
- [ ] Ноутбук можно выключить: `sing-box` + `tmux`/`claude` на VDS, `systemd` enabled.
- [ ] `curl https://api.ipify.org` **на VDS** = EXIT_IP кабинета, не IP VDS.
- [ ] RIPEstat → **AS9198**.
- [ ] SSH **из РФ** на IP хостера (ключ, порт 22/2222); VNC в панели проверен.
- [ ] SSH жив при `systemctl stop sing-box`.
- [ ] DNS без IP хостера (`resolvectl query` / `dig`); WebRTC — только если есть браузер на VDS.
- [ ] Локаль VDS UTC+5, `ru_KZ`/`kk_KZ` (§4).
- [ ] Слот dedicated, порт не ротационный.

Если KZ+9198 dedicated нет в кабинете — не подменять DC «из Алматы» и не брать rotating residential. Ждать слот / другого поставщика из таблицы §2.

### 3.8. Claude Code на этом VDS

**Да, будет работать**, если: Ubuntu 24.04 KVM, RAM **8 GB** (пол Anthropic — 4 GB, см. §3.4.1), исходящий трафик Claude — **AS9198**, не IP хостера в РФ.

Почему так: Anthropic отдаёт API и Claude.ai только из [списка стран](https://www.anthropic.com/supported-countries). **Kazakhstan есть, России нет.** Сырой Timeweb/Aeza в Москве для `api.anthropic.com` часто получает отказ по гео. Dedicated ISP AS9198 как раз ставит egress в разрешённую страну. Документация CLI: [setup](https://code.claude.com/docs/en/setup.md), [сеть и прокси](https://code.claude.com/docs/en/network-config), гайд на VPS: [virtua.cloud](https://www.virtua.cloud/learn/en/tutorials/run-claude-code-vps).

Важно: в официальном network-config написано **«Claude Code does not support SOCKS proxies»**. Не ставьте `HTTPS_PROXY=socks5://…`. Нужен именно **TUN** (§3.6): для процесса `claude` интернет выглядит как обычный default route, а наружу уходит SOCKS. Если TUN выключен — Claude уйдёт с IP VDS (РФ/хостинг) и сломается.

Установка (native installer, npm не нужен):

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Headless, без браузера на сервере:

- ключ Console: `export ANTHROPIC_API_KEY=…` ([console.anthropic.com](https://console.anthropic.com));
- или Pro/Max: OAuth-токен с машины с браузером, затем на VDS `CLAUDE_CODE_OAUTH_TOKEN`.

Проверка: `claude -p "reply with one word: ok"` под включённым sing-box. Сначала `curl -4 https://api.anthropic.com` / ipify = EXIT_IP 9198.

Держите сессию в `tmux`/`screen`, иначе SSH disconnect убьёт агента. Репозиторий клонируйте **на VDS**.

Риски: если dedicated IP уже в антифрод-базах как proxy — возможны 403; тогда замена IP у поставщика, не ротация. Не гоняйте парсинг с того же EXIT_IP.

### 3.9. Какие IDE с Claude Code на этом VDS

Claude Code — это **CLI на машине, откуда уходит API**. Anthropic смотрит IP **того процесса**, не окна редактора у вас в РФ. Значит IDE должна либо жить на VDS (за TUN), либо только рисовать UI, а `claude` запускать **на VDS**.

Официальные поверхности: [IDE integrations](https://code.claude.com/docs/en/ide-integrations), [JetBrains](https://code.claude.com/docs/en/jetbrains). Расширение **не умеет SOCKS** — как и CLI; нужен TUN.

| Схема | Что ставить | Claude Code | Заметки для вашего контура |
| --- | --- | --- | --- |
| **A. Только терминал** | `tmux` + `claude` по SSH | Да, эталон | Минимум RAM/GPU. GUI не нужен |
| **B. VS Code Remote-SSH** | VS Code/Cursor **на ноутбуке**, проект на VDS | CLI в **integrated terminal** на remote | Расширение Anthropic на Remote-SSH часто ломает пути ([issue](https://github.com/anthropics/claude-code/issues/20226)). Терминал `claude` — ок |
| **C. VS Code/Cursor на VDS** | `code-server` или полный VS Code + xrdp | Расширение `anthropic.claude-code` | API идёт с VDS через TUN. Нужны 4–8 GB и GUI/браузер |
| **D. JetBrains** | Gateway / Projector / IDE на VDS | Плагин + CLI в PATH на **том же** хосте | [Плагин](https://plugins.jetbrains.com/plugin/27310-claude-code-beta-): IntelliJ, PyCharm, WebStorm, GoLand, PhpStorm, Android Studio. Тяжелее VS Code |
| **E. Форки VS Code** | Cursor, VSCodium, Kiro, Devin Desktop | То же расширение или Open VSX | Cursor: `cursor:extension/anthropic.claude-code`. Свой чат Cursor ≠ Claude Code и с ноутбука в РФ упрётся в гео Anthropic |

**Надёжно из РФ без GUI на сервере:** ноутбук → Remote-SSH → на VDS в терминале `claude`. Файлы и API на VDS (KZ 9198). Расширение в сайдбаре — по желанию, не рассчитывать.

**Полноценная панель Claude в IDE:** ставьте VS Code/Cursor **на VDS** (code-server в браузере или RDP). Тогда и расширение, и CLI видят Linux-пути и тот же TUN.

Не подойдёт как основной путь:

- IDE только на ноутбуке в РФ, Claude локально, файлы через SFTP — egress из России, Anthropic режет.
- `HTTPS_PROXY=socks5://` в IDE — [официально нет SOCKS](https://code.claude.com/docs/en/network-config).
- Xcode / Visual Studio (не Code) — нет нормального плагина Claude Code; только CLI в терминале, если вообще соберёте toolchain на Linux VDS (Xcode — нет).

Практичный набор под тариф §3.4.1: **VS Code Remote-SSH + `claude` в tmux**. code-server — если нужна панель в браузере (лучше туннель на `127.0.0.1`). JetBrains — только если уже на них сидите и готовы к **16 GB**.

---

## 4. Локаль на VDS

С 1 марта 2024 в РК один пояс: **UTC+05:00**, без DST.

### Linux (основной случай)

```bash
sudo timedatectl set-timezone Asia/Almaty
sudo localectl set-locale LANG=ru_KZ.UTF-8
```

Проверка: `timedatectl`, `locale`, время как на [time.is/Almaty](https://time.is/Almaty).

Windows Server в этом контуре не берём (§3.4.1). Если всё же Windows: пояс **(UTC+05:00) Астана**, языки `kk-KZ` / `ru-KZ`.

Не включать второй VPN рядом с TUN.

---

## 5. Номер eSIM на ИИН (SMS, не интернет VDS)

Интернет VDS идёт через AS9198-прокси. Телефон нужен только для SMS.

Национальный формат: `8 777 123 45 67` или `7771234567`. Не российский `9xx`. Код зоны по-прежнему 7, отдельного `+997` нет.

| Код | Оператор |
| --- | --- |
| 701, 702 | Kcell |
| 775, 778 | Activ |
| 705, 771, 776, 777 | Beeline |
| 706 | IZI |
| 707, 747 | Tele2 |
| 700, 708 | Altel |

Местная eSIM (Beeline / Kcell / Tele2 / IZI): ИИН + eKYC в приложении. Туристическая data-eSIM номера не даёт.

1. `*#06#` — строка EID.
2. «Мой Beeline» / «My Kcell» / «Мой Tele2» → новый номер или замена на eSIM.
3. ИИН + биометрия документа, оплата Kaspi / карта РК.
4. QR сразу на свой телефон.
5. Привязка: [База мобильных граждан](https://egov.kz/cms/ru/services/pass1013_mcriap).

Горячие линии: Beeline `0611`, Kcell `0505`, Tele2 `0500`. Сайты: [beeline.kz](https://beeline.kz), [kcell.kz](https://kcell.kz), [tele2.kz](https://tele2.kz).

---

## 6. Источники

Инструкции «купи AS9198 dedicated в августе 2026» в открытом вебе нет. Слоты — только кабинет. Ниже живые гайды.

| Дата | Ссылка | Зачем |
| --- | --- | --- |
| Выгружено 14.08.2026 | [Oxylabs DISP](https://developers.oxylabs.io/help-center/getting-started/start-using-dedicated-isp-proxies) | Порт = IP, SOCKS5, не `:8000` |
| Выгружено 14.08.2026 | [Oxylabs location / RIPEstat](https://developers.oxylabs.io/products/proxies/dedicated-isp-proxies/self-service/location-settings) | ASN проверять в RIPEstat |
| Выгружено 14.08.2026 | [Oxylabs страны](https://developers.oxylabs.io/help-center/products-and-features/what-countries-do-oxylabs-proxies-cover) | KZ только в Buy Now |
| Выгружено 14.08.2026 | [Oxylabs DISP quick start](https://oxylabs.io/blog/dedicated-isp-proxies-quick-start-guide) | ASN при checkout |
| Выгружено 14.08.2026 | [Bright Data ISP](https://docs.brightdata.com/proxy-networks/isp/configure-your-proxy) | Dedicated, страна, не ASN |
| Выгружено 14.08.2026 | [Bright Data geo](https://docs.brightdata.com/api-reference/proxy/geolocation-targeting) | `-asn-` только Residential |
| Q2 2026 | [IPRoyal ISP Quick-Start](https://iproyal.com/quick-start-guides/static-residential-proxies/) | Extra Requirements, SOCKS5 12324 |
| 27.02.2026 | [IPRoyal FAQ ISP](https://help.iproyal.com/en/articles/7222102-are-the-proxies-from-real-residential-ip-addresses) | ASN ISP, хостинг на DC |
| Выгружено 14.08.2026 | [sing-box TUN](https://sing-box.sagernet.org/manual/proxy/client/), [tun](https://sing-box.sagernet.org/configuration/inbound/tun/) | Весь трафик VDS в SOCKS5 |
| Выгружено 14.08.2026 | [tun2socks](https://bigmike.help/en/devops/routing-all-system-traffic-through-a-socks5-proxy-using-tun2socks/) | Альтернатива TUN |
| Выгружено 14.08.2026 | [RIPEstat Network Info](https://stat.ripe.net/docs/data-api/api-endpoints/network-info) | origin AS по IP |
| 05.08.2026 PeeringDB | [AS9198](https://www.peeringdb.com/asn/9198) | Казахтелеком |
| Выгружено 14.08.2026 | [PS initial VPS](https://docs.ps.kz/ru/hosting/vps/getting-started/initial-vps-setup) | SSH на VDS; IP хостера не exit |
| Выгружено 14.08.2026 | [PS пиринги](https://docs.ps.kz/ru/data-center/data-center-overview/network-providers) | Пиринг с KT ≠ AS9198 на VPS |
| 2026 | [VPS с оплатой из РФ](https://vc.ru/toprate/2935681-zarubezhnyy-vps-s-oplatoy-iz-rossii) | Fornex, JustHost, AdminVPS, Timeweb, Hostiman |
| Май 2026 | [VPS с картой «Мир»](https://dtf.ru/top-raiting/4767988-luchshie-vps-vds-s-oplate-mir) | МИР/СБП у РФ-ориентированных хостеров |
| Август 2026 | [VPS без KYC](https://dtf.ru/top-raiting/5011159-luchshie-vps-vds-bez-kyc), [vc.ru](https://vc.ru/top-raiting/2879899-luchshie-vps-vds-bez-kyc) | Aeza, ISHosting, Fornex, Timeweb, FirstVDS |
| Август 2026 | [VDS для сайта](https://vc.ru/top-raiting/2314696-luchshie-vds-vps-dlya-arendy-servera-dlya-sayta) | Aeza, Timeweb Cloud, AdminVPS, VDSina |
| Tproger | [VPS в рублях](https://tproger.ru/articles/10-zarubezhnyh-vps--gde-mozhno-platit-v-rublyah---bez-seryh-shem) | Fornex, Koara, RuWeb и др. |
| 2026 | [DigitalOcean из РФ](https://vc.ru/services/2684194-oplata-digitalocean-v-rossii), [Hetzner из РФ](https://dtf.ru/howto/3920357-oplata-hetzner-v-rossii) | Почему не брать как основной VDS |

---

## 7. Юридическое

Идентификация SIM — Закон РК «О связи», только свой ИИН. Прокси — в рамках ToS сайтов. IMEI в сети РК регистрируется при местной SIM.
