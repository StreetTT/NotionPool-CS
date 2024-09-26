from utils import _Database, Entity
from dotenv import load_dotenv as LoadEnvVariables
from os import environ
LoadEnvVariables()


class NPCS(_Database):
    def __init__(self):
        super().__init__(
            environ.get("DB_USERNAME"), 
            environ.get("DB_PASSWORD"), 
            environ.get("DB_NAME")
        )
        self._Tables: dict[str,Entity] = {
                    "Person": Person(self),
                    "NotionApp": NotionApp(self),
                    "NotionWorkspace": NotionWorkspace(self),
                    "Modules": Modules(self),
                }
    
class Person(Entity):
    def __init__(self, database):
        super().__init__(database, """
        `homepage` VARCHAR(200) NOT NULL,
        `objectives` VARCHAR(200),
        `notes` VARCHAR(200),
        `assignments` VARCHAR(200),
        `assessments` VARCHAR(200),
        `modules` VARCHAR(200),
        `reading` VARCHAR(200),
        `start_year` VARCHAR(6),
        `person_id` VARCHAR(200) NOT NULL,
        PRIMARY KEY (`person_id`)""")


class NotionApp(Entity):
    def __init__(self, database):
        super().__init__(database, """
        `access_token` VARCHAR(200) NOT NULL,
        `token_type` VARCHAR(200) NOT NULL,
        `bot_id` VARCHAR(200) NOT NULL,
        `person_id` VARCHAR(200) NOT NULL,
        FOREIGN KEY (`person_id`) REFERENCES `Person`(`person_id`),
        PRIMARY KEY (`bot_id`)""")

class NotionWorkspace(Entity):
    def __init__(self, database):
        super().__init__(database, """
        `name` VARCHAR(200),
        `workspace_id` VARCHAR(200) NOT NULL,
        `icon` VARCHAR(200),
        `bot_id` VARCHAR(200) NOT NULL,
        FOREIGN KEY (`bot_id`) REFERENCES `NotionApp`(`bot_id`),
        PRIMARY KEY (`bot_id`)""")

class Modules(Entity):
    def __init__(self, database):
        super().__init__(database, """
        `module_id` VARCHAR(10) NOT NULL,
        `year` CHAR(6) NOT NULL,
        `semester` VARCHAR(6) NOT NULL,
        `person_id` VARCHAR(200) NOT NULL,
        `pushed` BOOLEAN NOT NULL,
        FOREIGN KEY (`person_id`) REFERENCES `Person`(`person_id`),
        PRIMARY KEY (`module_id`, `person_id`)""")
        