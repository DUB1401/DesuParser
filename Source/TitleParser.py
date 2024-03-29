from dublib.Methods import Cls, ReadJSON, RemoveRecurringSubstrings, WriteJSON
from Source.Functions import GetImageResolution
from dublib.WebRequestor import WebRequestor
from bs4 import BeautifulSoup
from time import sleep

import requests
import logging
import shutil
import json
import os
import re

class TitleParser:
	
	# Дополняет главы данными о слайдах.
	def __AmendChapters(self):
		# Запись в лог сообщения: дополнение глав.
		logging.info("Title: \"" + self.__Slug + "\". Amending...")
		# Количество дополненных глав.
		AmendedChaptersCount = 0
		# Количество глав.
		TotalChaptersCount = len(self.__Title["chapters"][self.__TitleID])
		
		# Для каждой главы.
		for Index in range(0, TotalChaptersCount):
			# Очистка консоли.
			Cls()
			# Вывод в терминал: прогресс дополнения.
			print(self.__Message + "Amending chapters: " + str(AmendedChaptersCount + 1) + " / " + str(TotalChaptersCount))
			# Буфер главы.
			Bufer = self.__Title["chapters"][self.__TitleID][Index]
			
			# Если в главе не описаны слайды.
			if Bufer["slides"] == []:
				# Дополнение слайдами.
				Bufer["slides"] = self.__GetChapterSlides(self.__GetChapterURI(Bufer["id"]), "Title: \"" + self.__Slug + "\". Volume " + str(Bufer["volume"]) + " chapter " + str(Bufer["number"]) + ".")
				# Запись в лог сообщения: данные о слайдах добавлены.
				logging.info("Title: \"" + self.__Slug + "\". Volume " + str(Bufer["volume"]) + " chapter " + str(Bufer["number"]) + " amended.")
				# Перезапись главы буфером.
				self.__Title["chapters"][self.__TitleID][Index] = Bufer
				# Инкремент количества дополненных глав.
				AmendedChaptersCount += 1
				# Если глава не последняя, выждать интервал.
				if Index + 1 != TotalChaptersCount: sleep(self.__Settings["delay"])
				
		# Запись в лог сообщения: дополнение глав.
		logging.info("Title: \"" + self.__Slug + "\". Amended chapters: " + str(AmendedChaptersCount) + ".")
		
	# Генерирует синтетически ID главы.
	def __BuildChapterID(self, Volume: int | str, Number: int | str) -> int:
		# Конвертирование номеров в строки.
		Volume = str(Volume).replace('.', "")
		Number = str(Number).replace('.', "")
		# Синтетический ID.
		ID = int(Volume + "0" + Number)
		
		return ID
	
	# Выставляет возрастное ограничение.
	def __CheckAgeLimit(self):
		
		# Если в жанрах указан хентай, задать возрастное ограничение.
		if "хентай" in self.__Title["genres"]:
			self.__Title["age-rating"] = 18
			
		else:
			self.__Title["age-rating"] = 0
	
	# Форматирует указанные настройками жанры в теги.
	def __FindTags(self):
		# Удаляемые жанры.
		GenresToDeleting = list()
		
		# Проход по всем жанрам и названиям жанров.
		for GenreIndex in range(0, len(self.__Title["genres"])):
			for TagName in list(self.__Settings["tags"].keys()):

				# Если название жанра совпадает с названием тега.
				if self.__Title["genres"][GenreIndex] == TagName.lower():
					# Запись жанра для последующего удаления.
					GenresToDeleting.append(self.__Title["genres"][GenreIndex])
					
					# Если жанр не нужно переименовать в тег.
					if self.__Settings["tags"][TagName.lower()] == None:
						self.__Title["tags"].append(self.__Title["genres"][GenreIndex])

					# Если жанр нужно переименовать в тег.
					else:
						self.__Title["tags"].append(self.__Settings["tags"][TagName.lower()])

		# Удаление ненужных жанров.
		for Genre in GenresToDeleting:
			self.__Title["genres"].remove(Genre)
			
	# Возвращает структуру главы.
	def __GetChapter(self, Chapter: dict) -> dict:
		# Структура главы.
		ChapterStruct = {
			"id": Chapter["id"],
			"volume": Chapter["volume"],
			"number": Chapter["number"],
			"name": Chapter["name"],
			"is-paid": False,
			"translator": None,
			"slides": list()
		}

		return ChapterStruct
	
	# Возвращает список слайдов главы.
	def __GetChapterSlides(self, ChapterURI: str, LoggingInfo: str) -> list[dict]:
		# Список слайдов.
		Slides = list()
		# Запрос страницы.
		Response = self.__Requestor.get(f"https://desu.me/manga/{self.__Slug}/{ChapterURI}/rus#page=1")

		# Если запрос успешен.
		if Response.status_code == 200:
			# Парсинг HTML кода страницы.
			Soup = BeautifulSoup(Response.text, "html.parser")
			# Поиск всех блоков JavaScript.
			Scripts = Soup.find_all("script", {"type": "text/javascript"})
			# Данные.
			Data = None
			# Директория на сервере.
			Dir = None
			
			# Для каждого блока.
			for Script in Scripts:
				
				# Если скрипт содержит слайды.
				if self.__Slug in str(Script):
					# Приведение данных к списку списокв.
					Data = json.loads(str(Script).split("images:")[-1].split("page:")[0].strip().strip(","))
					# Получение директории.
					Dir = str(Script).split("dir:")[-1].split("mangaUrl:")[0].strip().strip("\",")
			
			# Если удалось получить список слайдов.
			if Data != None and Dir != None:
				
				# Для каждого элемента списка.
				for SlideIndex in range(0, len(Data)):
					# Буфер слайда.
					Slide = {
						"index": SlideIndex + 1,
						"link": f"https:" + Dir + Data[SlideIndex][0],
						"width": Data[SlideIndex][1],
						"height": Data[SlideIndex][2]
					}
					# Запись данных о слайде.
					Slides.append(Slide)
			
		return Slides
	
	# Возвращает URI главы.
	def __GetChapterURI(self, ChapterID: int | str) -> str | None:
		# URI главы.
		ChapterURI = None
		
		# Для каждой описанной главы.
		for Chapter in self.__ChaptersData:
			
			# Если ID главы совпадает со словарём описания, то записать URI.
			if Chapter["id"] == int(ChapterID):
				ChapterURI = Chapter["URI"]
				
		return ChapterURI
	
	# Получает данные о главах.
	def __GetChapters(self):
		# Список глав.
		Chapters = list()		

		# Для каждой главы.
		for Chapter in self.__ChaptersData:
			# Получение данных о главе.
			Chapters.append(self.__GetChapter(Chapter))
			
		# Запись инвертированного списка глав.
		self.__Title["chapters"][self.__TitleID] = list(reversed(Chapters))
		
	# Получает названия глав.
	def __GetChaptersData(self, Soup: BeautifulSoup):
		# Поиск контейнера списка глав.
		ChaptersContainer = Soup.find("ul", {"class": "chlist"})
		# Парсинг контейнера списка глав.
		Soup = BeautifulSoup(str(ChaptersContainer), "html.parser")
		# Парсинг ссылок на главы.
		ChaptersLinks = Soup.find_all("a")
		
		# Для каждой ссылки.
		for Link in ChaptersLinks:
			# Буфер данных главы.
			Bufer = {
				"id": None,
				"name": None,
				"volume": None,
				"number": None,
				"URI": None
			}
			# Получение данных главы.
			Bufer["volume"] = re.search(r"Том \d+(\.\d+)?", Link.get_text())[0].replace("Том ", "")
			Bufer["number"] = re.search(r"Глава \d+(\.\d+)?", Link.get_text())[0].replace("Глава ", "")
			Bufer["id"] = self.__BuildChapterID(Bufer["volume"], Bufer["number"])
			Bufer["URI"] = Link["href"].replace(f"manga/{self.__Slug}/", "").replace("/rus", "")
			# Поиск блока с названием главы.
			ChapterNameBlock = BeautifulSoup(str(Link), "html.parser").find("span", {"class": "title nowrap"})
			
			# Если блок с названием главы присутствует.
			if ChapterNameBlock != None:
				# Запись названия главы.
				Bufer["name"] = ChapterNameBlock.get_text().lstrip(" -")
				
			# Запись данных о главе.
			self.__ChaptersData.append(Bufer)
	
	# Возвращает структуру обложки.
	def __GetCoverData(self, PageHTML: str) -> dict:
		# Контейнер обложек.
		CoversList = list()
		# Парсинг HTML кода тела страницы.
		Soup = BeautifulSoup(PageHTML, "html.parser")
		# Поиск HTML элемента обложки.
		CoverHTML = Soup.find("img", {"itemprop": "image"})
		# Описательная структура обложки.
		Cover = {
			"link": None,
			"filename": None,
			"width": None,
			"height": None
		}

		# Если обложка есть, определить её URL и название.
		if "src" in CoverHTML.attrs.keys():

			# Если у обложки есть источник.
			if str(CoverHTML["src"]) != "":
				Cover["link"] = "https://desu.me/" + str(CoverHTML["src"])
				Cover["filename"] = Cover["link"].split('/')[-1]
				CoversList.append(Cover)

				# Используемое имя тайтла: ID или алиас.
				UsedTitleName = str(self.__ID) if self.__Settings["use-id-instead-slug"] == True else self.__Slug
				
				# Если включено определение разрешение обложки.
				if self.__Settings["sizing-covers"] == True:
					# Определение разрешения.
					Resolution = GetImageResolution(self.__Settings["covers-directory"] + UsedTitleName + "/" + Cover["filename"])
					# Заполнение разрешения.
					Cover["width"] = Resolution["width"]
					Cover["height"] = Resolution["height"]

			# Если у обложки нет источника.
			else:
				# Запись в лог предупреждения: обложка отсутствует.
				logging.warning("Title: \"" + self.__Slug + "\". Cover missing.")

		return CoversList

	# Возвращает список тегов.
	def __GetGenres(self, PageHTML: str) -> list:
		# Список жанров.
		Genres = list()
		# Парсинг HTML кода тела страницы.
		Soup = BeautifulSoup(PageHTML, "html.parser")
		# Поиск контейнера жанров.
		TagsContainer = Soup.find("ul", {"class": "tagList"})
		# Поиск контейнеров ссылок на жанры.
		AllGenres = BeautifulSoup(str(TagsContainer), "html.parser").find_all("a")
		
		# Для названия каждого жанра удалить лишние символы.
		for Genre in AllGenres:
			Genres.append(Genre.get_text().lower())
		
		return Genres
	
	# Дополняет тайтл описательными данными.
	def __GetTitleData(self):
		# URL всех глав тайтла или похожих тайтлов.
		TitleURL = "https://desu.me/manga/" + self.__Slug
		
		# Если процесс парсинга активен.
		if self.__IsActive == True:
			# HTML код страницы.
			PageHTML = self.__Requestor.get(TitleURL).text
			# Парсинг HTML кода страницы.
			Soup = BeautifulSoup(PageHTML, "html.parser")
			# Получение данных об обложке.
			self.__Title["covers"] = self.__GetCoverData(PageHTML)
			# Поиск русского названия.
			self.__Title["ru-name"] = Soup.find("span", {"class": "rus-name"}).get_text()
			# Поиск английского названия.
			self.__Title["en-name"] = Soup.find("span", {"class": "name"}).get_text()
			# Поиск блока альтернативных названий.
			AnotherNamesBlock = Soup.find("span", {"class": "alternativeHeadline"})
			# Поиск описания.
			self.__Title["description"] = RemoveRecurringSubstrings(Soup.find("div", {"class": "prgrph"}).get_text().replace("<br>", "\n").strip(), "\n")
			# Поиск контейнеров данных описания.
			LineContainers = Soup.find_all("div", {"class": "line-container"})
			# Запись информации об отсутствии лицензии.
			self.__Title["is-licensed"] = False
			# Получение тегов.
			self.__Title["genres"] = self.__GetGenres(PageHTML)
			# Выставление возрастного ограничения.
			self.__CheckAgeLimit()
			# Переопределение жанров в теги.
			self.__FindTags()
			# Определения статусов.
			Statuses = {
				"": "ANNOUNCED",
				"продолжается": "ONGOING",
				"": "ABANDONED",
				"завершён": "COMPLETED",
				"": "UNKNOWN"
			}
			# Определения типов.
			Types = {
				"Манга": "MANGA",
				"Манхва": "MANHWA",
				"Маньхуа": "MANHUA",
				"": "WESTERN_COMIC",
				"": "RUS_COMIC",
				"": "INDONESIAN_COMIC",
				"": "OEL",
				"": "UNKNOWN"
			}
			# Генерация ветви.
			self.__Title["branches"].append({"id": int(self.__TitleID), "chapters-count": None})
			self.__Title["chapters"][self.__TitleID] = list()
			# Получение данных о главах.
			self.__GetChaptersData(Soup)
			
			# Если у тайтла есть альтернативные названия.
			if AnotherNamesBlock != None:
				self.__Title["another-names"] = AnotherNamesBlock.get_text().split(", ")

			# Для каждого контейнера.
			for Container in LineContainers:
				
				# Если контенйер содержит год публикации.
				if "Статус:" in str(Container):
					# Получение годов выпуска.
					Years = BeautifulSoup(str(Container), "html.parser").find("div", {"class": "value"}).get_text()
					# Поиск года выпуска регулярным выражением.
					Match = re.search("\d{4}", str(Years))
					# Запись года публикации.
					self.__Title["publication-year"] = None if Match[0] == None else int(Match[0])
				
				# Если контейнер содержит статус.
				elif "Перевод:" in str(Container):
					# Получение статуса.
					Status = BeautifulSoup(str(Container), "html.parser").find("div", {"class": "value"}).get_text().strip()
					
					# Если статус определён.
					if Status in Statuses.keys():
						# Записать статус.
						self.__Title["status"] = Statuses[Status]
						
					else:
						# Записать неизвестный статус.
						self.__Title["status"] = "UNKNOWN"
						
				# Если контейнер содержит тип.
				elif "Тип:" in str(Container):
					# Получение типа.
					Type = BeautifulSoup(str(Container), "html.parser").find("div", {"class": "value"}).get_text().strip()
					
					# Если тип определён.
					if Type in Types.keys():
						# Записать тип.
						self.__Title["type"] = Types[Type]
						
					else:
						# Записать неизвестный тип.
						self.__Title["type"] = "UNKNOWN"		
					
			# Запись в лог сообщения: получено описание тайтла.
			logging.info("Title: \"" + self.__Slug + "\". Request title description... Done.")
			
	# Выполняет слияние ветви локального файла и полученной с сервера.
	def __MergeBranches(self, LocalFilename: str):
		# Чтение локального файла.
		LocalTitle = ReadJSON("Titles/" + LocalFilename + ".json")
		# Список локальных глав.
		LocalChaptersList = LocalTitle["chapters"][str(LocalTitle["branches"][0]["id"])]
		
		# Если включён режим перезаписи.
		if self.__ForceMode == True:
			# Запись в лог сообщения: найден локальный описательный файл тайтла.
			logging.info("Title: \"" + self.__Slug + "\". Local JSON already exists. Will be overwritten...")
			
		else:
			# Запись в лог сообщения: найден локальный описательный файл тайтла.
			logging.info("Title: \"" + self.__Slug + "\". Local JSON already exists. Trying to merge...")

		# Произвести слияние информации о слайдах из локального файла с данными, полученными с сервера.
		for BranchID in self.__Title["chapters"].keys():
			for ChapterIndex in range(0, len(self.__Title["chapters"][BranchID])):
				# ID текущей главы.
				ChapterID = self.__Title["chapters"][BranchID][ChapterIndex]["id"]

				# Поиск данных о слайдах в локальных главах.
				for LocalChapter in LocalChaptersList:

					# Если ID обрабатываемой главы совпал с ID локальной главы.
					if ChapterID == LocalChapter["id"]:
						# Копирование данных о слайдах.
						self.__Title["chapters"][BranchID][ChapterIndex]["slides"] = LocalChapter["slides"]
						# Инкремент количества слияний.
						self.__MergedChaptersCount += 1

		# Запись в лог сообщения: завершение слияния.
		logging.info("Title: \"" + self.__Slug + "\". Merged chapters: " + str(self.__MergedChaptersCount) + ".")

	# Конструктор: строит структуру описательного файла тайтла и проверяет наличие локальных данных.
	def __init__(self, Settings: dict, Slug: str, ForceMode: bool = False, Message: str = "", Amending: bool = True):

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Количество выполненных слияний глав.
		self.__MergedChaptersCount = 0
		# Список данных глав тайтла.
		self.__ChaptersData = list()
		# Состояние: включена ли перезапись файлов.
		self.__ForceMode = ForceMode
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Запросчик.
		self.__Requestor = WebRequestor()
		# Состояние: доступен ли тайтл.
		self.__IsActive = True
		# ID тайтла.
		self.__TitleID = Slug.split(".")[-1]
		# Описательная структура тайтла.
		self.__Title = {
			"format": "dmp-v1",
			"site": "desu.me",
			"id": int(self.__TitleID),
			"slug": Slug,
			"covers": list(),
			"ru-name": None,
			"en-name": None,
			"another-names": list(),
			"author": None,
			"publication-year": None,
			"age-rating": None,
			"description": None,
			"type": "ANOTHER",
			"status": "ANOTHER",
			"is-licensed": None,
			"series": list(),
			"genres": list(),
			"tags": list(),
			"branches": list(),
			"chapters": dict()
		}
		# Алиас тайтла.
		self.__Slug = Slug
		# Сообщение из внешнего обработчика.
		self.__Message = Message + "Current title: " + self.__Slug + "\n\n"
		
		# Инициализация запросчика.
		self.__Requestor.initialize()

		#---> Получение данных о тайтле.
		#==========================================================================================#
		# Запись в лог сообщения: парсинг начат.
		logging.info("Title: \"" + self.__Slug + "\". Parcing...")
		# Получение описательных данных тайтла.
		self.__GetTitleData()

		# Если включена полная обработка файла.
		if Amending == True and self.__IsActive == True:
			# Получение данных глав тайтла.
			self.__GetChapters()
			
			# Если включён режим перезаписи.
			if ForceMode == False:

				# Слияние с локальным описательным файлом.
				if os.path.exists(self.__Settings["titles-directory"] + self.__Slug + ".json"):
					self.__MergeBranches(self.__Slug)
					
				elif os.path.exists(self.__Settings["titles-directory"] + self.__TitleID + ".json"):
					self.__MergeBranches(self.__TitleID)

			# Дополняет главы данными о слайдах.
			self.__AmendChapters()
			# Подсчёт количества глав.
			self.__Title["branches"][0]["chapters-count"] = len(self.__Title["chapters"][str(self.__Title["branches"][0]["id"])])
			
	# Загружает обложку тайтла.
	def downloadCover(self):
			
		# Если удалось получить доступ к тайтлу.
		if self.__IsActive == True:
			# Счётчик загруженных обложек.
			DownloadedCoversCounter = 0
			# Используемое имя тайтла: ID или алиас.
			UsedTitleName = None
			# Очистка консоли.
			Cls()
			# Вывод в консоль: сообщение из внешнего обработчика и алиас обрабатываемого тайтла.
			print(self.__Message, end = "")
		
			# Создание директории обложек, если таковая отсутствует.
			if os.path.exists(self.__Settings["covers-directory"]) == False:
				os.makedirs(self.__Settings["covers-directory"])

			# Установка используемого имени тайтла.
			if self.__Settings["use-id-instead-slug"] == False:
				UsedTitleName = self.__Slug
			
			else:
				UsedTitleName = self.__TitleID

			# Для каждой обложки.
			for CoverIndex in range(0, len(self.__Title["covers"])):
				# URL обложки.
				CoverURL = self.__Title["covers"][CoverIndex]["link"]
				# Название файла обложки.
				CoverFilename = self.__Title["covers"][CoverIndex]["filename"]
				# Ответ запроса.
				Response = None

				# Если включён режим перезаписи, то удалить файл обложки.
				if self.__ForceMode == True:
					
					# Удалить файл обложки.
					if os.path.exists(self.__Settings["covers-directory"] + self.__Slug + "/" + CoverFilename):
						shutil.rmtree(self.__Settings["covers-directory"] + self.__Slug) 
					elif os.path.exists(self.__Settings["covers-directory"] + self.__TitleID + "/" + CoverFilename):
						shutil.rmtree(self.__Settings["covers-directory"] + self.__TitleID) 

				# Удаление папки для обложек с алиасом в названии, если используется ID.
				if self.__Settings["use-id-instead-slug"] == True and os.path.exists(self.__Settings["covers-directory"] + self.__Slug + "/" + CoverFilename):
					shutil.rmtree(self.__Settings["covers-directory"] + self.__Slug)

				# Удаление папки для обложек с ID в названии, если используется алиас.
				if self.__Settings["use-id-instead-slug"] == False and os.path.exists(self.__Settings["covers-directory"] + self.__TitleID + "/" + CoverFilename):
					shutil.rmtree(self.__Settings["covers-directory"] + self.__TitleID)

				# Проверка существования файла обложки.
				if os.path.exists(self.__Settings["covers-directory"] + UsedTitleName + "/" + CoverFilename) == False:
					# Вывод в терминал URL загружаемой обложки.
					print("Downloading cover: \"" + CoverURL + "\"... ", end = "")
					# Выполнение запроса.
					Response = requests.get(CoverURL)

					# Проверка успешности запроса.
					if Response.status_code == 200:

						# Создание папки для обложек.
						if os.path.exists(self.__Settings["covers-directory"]) == False:
							os.makedirs(self.__Settings["covers-directory"])

						# Создание папки для конкретной обложки.
						if os.path.exists(self.__Settings["covers-directory"] + UsedTitleName) == False:
							os.makedirs(self.__Settings["covers-directory"] + UsedTitleName)

						# Открытие потока записи.
						with open(self.__Settings["covers-directory"] + UsedTitleName + "/" + CoverFilename, "wb") as FileWrite:
							# Запись изображения.
							FileWrite.write(Response.content)
							# Инкремент счётчика загруженных обложек.
							DownloadedCoversCounter += 1
							# Вывод в терминал сообщения об успешной загрузке.
							print("Done.")

					else:
						# Запись в лог сообщения о неудачной попытке загрузки обложки.
						logging.error("Title: \"" + self.__Slug + "\". Unable download cover: \"" + CoverURL + "\". Response code: " + str(Response.status_code) + ".")
						# Вывод в терминал сообщения об успешной загрузке.
						print("Failure!")

				else:
					# Вывод в терминал: URL загружаемой обложки.
					print("Cover already exist: \"" + CoverURL + "\". Skipped. ")

			# Запись в лог сообщения: количество загруженных обложек.
			logging.info("Title: \"" + self.__Slug + "\". Covers downloaded: " + str(DownloadedCoversCounter) + ".")

	# Сохраняет локальный JSON файл.
	def save(self):
		
		# Если удалось получить доступ к тайтлу.
		if self.__IsActive == True:
			# Используемое имя тайтла: ID или алиас.
			UsedTitleName = None

			# Создание директории тайтлов, если таковая отсутствует.
			if os.path.exists(self.__Settings["titles-directory"]) == False:
				os.makedirs(self.__Settings["titles-directory"])

			# Установка используемого имени тайтла.
			if self.__Settings["use-id-instead-slug"] == False:
				UsedTitleName = self.__Title["slug"]
			else:
				UsedTitleName = self.__TitleID

			# Сохранение локального файла JSON.
			WriteJSON(self.__Settings["titles-directory"] + UsedTitleName + ".json", self.__Title)

			# Запись в лог сообщения: создан или обновлён локальный файл.
			if self.__MergedChaptersCount > 0:
				logging.info("Title: \"" + self.__Slug + "\". Updated.")
				
			else:
				logging.info("Title: \"" + self.__Slug + "\". Parced.")