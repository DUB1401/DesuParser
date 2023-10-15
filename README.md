# Desu Parser
**Desu Parser** – это кроссплатформенный скрипт для получения данных с сайта [Desu](https://desu.me/) в формате JSON. Он позволяет записать всю информацию о конкретной манге, а также её главах и содержании глав. Структура описательного файла представлена [здесь](Examples/DMP-V1.md).

## Порядок установки и использования
1. Загрузить последний релиз. Распаковать.
2. Установить Python версии не старше 3.10. Рекомендуется добавить в PATH.
3. В среду исполнения установить следующие пакеты: [dublib](https://github.com/DUB1401/dublib), [webdriver_manager](https://github.com/SergeyPirogov/webdriver_manager), [BeautifulSoup4](https://launchpad.net/beautifulsoup), [Selenium](https://github.com/SeleniumHQ/selenium).
```
pip install git+https://github.com/DUB1401/dublib
pip install webdriver_manager
pip install BeautifulSoup4
pip install Selenium
```
Либо установить сразу все пакеты при помощи следующей команды, выполненной из директории скрипта.
```
pip install -r requirements.txt
```
4. Настроить скрипт путём редактирования _Settings.json_.
5. Установить браузер [Google Chrome](https://www.google.com.iq/chrome/) в стандартную директорию на Windows, либо использовать _*.deb_ или _*.rpm_ пакет на Linux.
6. Открыть директорию со скриптом в терминале. Можно использовать метод `cd` и прописать путь к папке, либо запустить терминал из проводника.
7. Указать для выполнения главный файл скрипта `dp.py`, передать ему команду вместе с параметрами, нажать кнопку ввода и дождаться завершения работы.

# Консольные команды
```
collect
```
Помещает список алиасов тайтлов, обновлённых на сайте за последние два дня, в файл _Collection.txt_.
___
```
getcov [MANGA_SLUG] [FLAGS]
```
Загружает обложки конкретного тайтла.

**Список специфических флагов:**
* _**-f**_ – включает перезапись уже загруженных обложек.
___
```
parce [MANGA_SLUG] [FLAGS] [KEYS]
```
Проводит парсинг тайтла с указанным алиасом в JSON формат и загружает его обложки. В случае, если файл тайтла уже существует, дополнит его новыми данными. 

**Список специфических флагов:**
* _**MANGA\_SLUG**_:
	* _**-collection**_ – указывает на то, что список тайтлов для парсинга необходимо взять из файла _Collection.txt_ (заменяет собой алиас тайтла).
* _**-f**_ – включает перезапись уже загруженных обложек и существующих JSON файлов.

**Список специфических ключей:**
* _**--from**_ – указывает, с момента обнаружение какого алиаса необходимо начать парсинг коллекции.
___
```
update [FLAGS] [KEYS]
```
Проводит парсинг тайтлов, обновлённых за последние два дня.

**Список специфических флагов:**
* _**-f**_ – включает перезапись уже загруженных обложек и существующих JSON файлов;
* _**-local**_ – обновляет все локальные файлы JSON.

**Список специфических ключей:**
* _**--from**_ – указывает алиас тайтла, с момента обнаружения которого в списке обновляемых тайтлов необходимо начать обработку обновлений, а eсли таковой не был обнаружен, скрипт пропустит все обновления.

## Неспецифические флаги
Данный тип флагов работает при добавлении к любой команде и выполняет отдельную от оной функцию.
* _**-s**_ – выключает компьютер после завершения работы скрипта.

# Settings.json
```JSON
"sizing-images": false
```
Указывает, нужно ли определять и записывать в JSON разрешение обложки и слайдов.
___
```JSON
"use-id-instead-slug": false
```
При включении данного параметра файлы JSON и директория обложек тайтла будут названы по ID произведения (коим считается ID первой главы тайтла), а не по алиасу.
___
```JSON
"covers-directory": ""
```
Указывает, куда сохранять обложки тайтлов. При пустом значении будет создана папка _Covers_ в исполняемой директории скрипта. Рекомендуется оформлять в соответствии с принципами путей в Linux, описанными [здесь](http://cs.mipt.ru/advanced_python/lessons/lab02.html#cd).
___
```JSON
"titles-directory": ""
```
Указывает, куда сохранять JSON-файлы тайтлов. При пустом значении будет создана папка Titles в исполняемой директории скрипта. Рекомендуется оформлять в соответствии с принципами путей в Linux, описанными [здесь](http://cs.mipt.ru/advanced_python/lessons/lab02.html#cd).
___
```JSON
"tags": {
	"название жанра": "название тега",
	"название жанра": null
}
```
В данном разделе можно указать список жанров, которые будут помечены как теги, а также, при необходимости, задать для них новые названия. Переопределённые жанры удаляются из оригинального списка.
___
```JSON
"disable-ssl-verification": false
```
Отключает верификацию SSL для веб-драйвера. Помогает избежать исключения, возникающего из-за ограничений в вашей сети: `requests.exceptions.ConnectionError: Could not reach host. Are you offline?`
___
```JSON
"adblock": false
```
Позволяет включить расширение [AdBlock Plus](https://gitlab.com/eyeo/adblockplus/abc/webext-ad-filtering-solution), что может ускорить обработку некоторых страниц [Desu](https://desu.me/).
___
```JSON
"timeout": 75
```
Указывает, через сколько секунд загрузка вкладки или выполнение скрипта считаются неудачными и инициализируют повторную попытку доступа.

Рекомендуемое значение: не менее 75 секунд (так как стандартное время отправки сервисом [nginx](https://nginx.org) ошибки 504 составляет 60 секунд, а время отклика сайта иногда доходит до 15 секунд).
___
```JSON
"retry-tries": 3
```
Указывает, сколко раз проводить повторные попытки при ошибке загрузки страницы.
___
```JSON
"debug": false
```
Переключает отображение окна браузера во время загрузки страниц через [Selenium](https://github.com/SeleniumHQ/selenium).

# Благодарность
* [AdBlock Plus](https://gitlab.com/eyeo/adblockplus/abc/webext-ad-filtering-solution) – расширение для браузеров, блокирующее рекламу и вспылвающие окна (в модификации [DUB1401](https://github.com/DUB1401): _отключена страница приветствия_).

_Copyright © DUB1401. 2023._
