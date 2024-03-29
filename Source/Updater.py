from dublib.WebRequestor import WebRequestor
from dublib.Methods import Cls
from bs4 import BeautifulSoup
from time import sleep

class Updater:
	
	# Проверяет, обновлён ли тайтл за последние двое суток.
	def __IsUpdatedInTwoDays(self, TitleBlock: str) -> bool:
		# Состояние: обновлён ли тайтл.
		IsUpdated = False
		# Получение текста последнего блока с информацией.
		Date = BeautifulSoup(TitleBlock, "html.parser").find_all("dd")[-1].get_text().lower()
		
		# Если дата содержит слова "сегодня" или "вчера", то переключить статус.
		if "сегодня" in Date or "вчера" in Date:
			IsUpdated = True
			
		return IsUpdated

	# Конструктор: задаёт глобальные настройки и менеджер навигации.
	def __init__(self, Settings: dict):

		#---> Генерация свойств.
		#==========================================================================================#
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Запросчик.
		self.__Requestor = WebRequestor()
		
		# Инициализация запросчика.
		self.__Requestor.initialize()

	# Возвращает список алиасов обновлённых тайтлов.
	def getUpdatesList(self) -> list:
		# Список алиасов обновлённых тайтлов.
		Updates = list()
		# Индекс текущей страницы.
		PageIndex = 1
		# Состояние: получены ли все обновления.
		IsAllUpdatesRecieved = False
		
		# Загружать страницы каталога последовательно.
		while IsAllUpdatesRecieved == False:
			# Список блоков новых глав, соответствующих заданному периоду.
			UpdatedTitlesBlocks = list()
			# Очистка консоли.
			Cls()
			# Вывод в консоль: сканируемая страница.
			print("Scanning page: " + str(PageIndex))
			# HTML код страницы.
			BodyHTML = self.__Requestor.get("https://desu.me/manga/?page=" + str(PageIndex)).text
			# Парсинг HTML кода страницы.
			Soup = BeautifulSoup(BodyHTML, "html.parser")
			# Поиск всех блоков обновлений.
			TitlesBlocks = Soup.find_all("li", {"class": "primaryContent memberListItem"})
			# Инкремент индекса страницы.
			PageIndex += 1
			
			# Для каждого блока обновления на странице каталога.
			for Block in TitlesBlocks:
				
				# Если дата загрузки главы соответствует заданному периоду.
				if self.__IsUpdatedInTwoDays(str(Block)) == True:
					UpdatedTitlesBlocks.append(str(Block))

				# Если дата загрузки главы вышла за пределы заданного периода.
				else:
					IsAllUpdatesRecieved = True
					
			# Если достигнута последняя страница.
			if len(TitlesBlocks) == 0:
				IsAllUpdatesRecieved = True

			# Для каждого блока новой главы, соответствующего заданному периоду.
			for Block in UpdatedTitlesBlocks:
				# Парсинг блока главы.
				Soup = BeautifulSoup(Block, "html.parser")
				# Поиск ссылки на тайтл.
				TitleLink = Soup.find("a")
				# Получение алиаса.
				Slug = TitleLink["href"].replace("manga/", "").strip('/')
				# Сохранение алиаса.
				Updates.append(Slug)
				
			# Если не все обновления получены, выждать интервал.
			if IsAllUpdatesRecieved == False: sleep(self.__Settings["delay"])
			
		return Updates