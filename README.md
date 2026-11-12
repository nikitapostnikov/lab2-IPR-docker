# Лабораторная работа №2: Docker - Контейнеризация приложений #

## Цель работы ##

Научиться создавать Docker образы для собственных приложений, работать с Docker Hub и контейнеризировать существующие проекты.

## Ход выполнения ##
**1. Dockerfile и .dockerignore**

В рамках данной лабораторной работы я создал Docker с контейнером для визуального веб - проекта, представляющего собой крутящийся пончик (тор) с возможностью изменения скорости вращения, реализованного на python-flask и numpy.

Получение образа через Docker Hub: **pull nikpos0fficial/ponchiq:1.0.0**; ссылка на образ:  https://hub.docker.com/r/nikpos0fficial/ponchiq

Схема  Docker - а:

    douckerlabb
    |
    |_.dockerignore
    |_APP_README.md             //отчёт по лабораторной работе
    |_app.py                    //само приложение
    |_Dockerfile
    |_requirements.txt          //файл зависимостей

--

    Dockerfile:

        FROM python:3.14-slim

        WORKDIR /ponchiq

        COPY requirements.txt .

        RUN pip install --no-cache-dir -r requirements.txt

        COPY app.py .

        EXPOSE 8080

        CMD ["python","app.py"]

Методы оптимизации Dockerfile:
+ slim - версия python => уменьшенный размер языка
+ --no-cache-dir при установке зависимостей => не выделяется лишнее место на кэш зависимостей
+ используется .dockerignore, чтобы не класть в Docker лишнее:

        .dockerignore:

            .git

            APP_README.md

            __pycache__


Так как из сторонних библиотек используются только Flask и numpy, то файл зависимостей requirements.txt содержит только их:

    requirements.txt

        Flask==3.1.3
        numpy==2.5.2

Для запуска используется CMD в exec-json форме, запускающий сам веб - сервис (app.py):

    CMD ["python","app.py"]

**2. Работающее приложение**

Создание докера по образу и использование его с помощью pull с Docker Hub


    ...> docker login
    ...
    Login Succeeded

    ...> docker build -t nikpos0fficial/ponchiq:1.0.0 .     /* создание образа (-t => имя и тэг образа; . => текущая папка, в неё производится сборка Docker-a) */
    [+] Building 3.1s (11/11) FINISHED
    ...
    View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/8vq05str4godlncgpcrckbtgy

    ...> docker push nikpos0fficial/ponchiq:1.0.0   //локально созданный Docker передается на Docker Hub
    The push refers to repository [docker.io/nikpos0fficial/ponchiq]
    128ed5fb5f8e: Pushed
    ...
    01e22d713b37: Layer already exists
    1.0.0: digest: sha256:6ac7453737f284bb9e2fbf5bf66d79bdd827a461055ae665ca208f07f67ea7de size: 856

    ...> docker rmi nikpos0fficial/ponchiq:1.0.0    //Docker удаляется локально, но при этом он есть на Docker Hub
    Untagged: nikpos0fficial/ponchiq:1.0.0
    Deleted: sha256:6ac7453737f284bb9e2fbf5bf66d79bdd827a461055ae665ca208f07f67ea7de

    ...> docker pull nikpos0fficial/ponchiq:1.0.0   //Берем на машину Docker с удаленного Docker Hub
    1.0.0: Pulling from nikpos0fficial/ponchiq
    ...
    Status: Downloaded newer image for nikpos0fficial/ponchiq:1.0.0
    docker.io/nikpos0fficial/ponchiq:1.0.0

    ...> docker run -d -p 8080:8080 nikpos0fficial/ponchiq:1.0.0    /*Запуск (-d => detatched - на фоне, так как веб - сервис, иначе будет выводить запросы при изменении ползунка скорости вращения пончика, -p 8080:8080 => перенаправление с порта 8080 хоста на порт 8080 контейнера - он же проброс портов), с этого момента сайт успешно работает по адресу http://localhost:8080/  */
    c3a3f5d911a9bf0c41ead8dd245958561c7cadabb597d97d7385e99aced6c243

    ...> docker ps //активные контейеры
    CONTAINER ID   IMAGE                          COMMAND           CREATED         STATUS         PORTS                                         NAMES
    c3a3f5d911a9   nikpos0fficial/ponchiq:1.0.0   "python app.py"   8 seconds ago   Up 8 seconds   0.0.0.0:8080->8080/tcp, [::]:8080->8080/tcp   confident_shannon

    ...> docker stop c3a3f5d911a9 //остановка контейнера (не удаление)
    c3a3f5d911a9

    ...> docker ps -a //все контейнеры => -a =all (у нашего контейнера виден "Extited..." - "Вышел..." дословно)
    CONTAINER ID   IMAGE                          COMMAND           CREATED         STATUS                        PORTS     NAMES
    c3a3f5d911a9   nikpos0fficial/ponchiq:1.0.0   "python app.py"   3 minutes ago   Exited (137) 35 seconds ago             confident_shannon

    ...> docker rm c3a3f5d911a9 //удаление контейнера
    c3a3f5d911a9

    ...> docker rmi nikpos0fficial/ponchiq:1.0.0 //удаление Docker-a
    Untagged: nikpos0fficial/ponchiq:1.0.0
    Deleted: sha256:6ac7453737f284bb9e2fbf5bf66d79bdd827a461055ae665ca208f07f67ea7de


**3.Bind Mount для разработки**

Запуск с bind mount осуществляется через  **docker run -d -p 8080:8080 -v "$(PWD):/ponchiq" nikpos0fficial/ponchiq:1.0.0**:

    ...> docker pull nikpos0fficial/ponchiq:1.0.0   //берем образ из Docker Hub                                  
    1.0.0: Pulling from nikpos0fficial/ponchiq
    ...
    Status: Downloaded newer image for nikpos0fficial/ponchiq:1.0.0
    docker.io/nikpos0fficial/ponchiq:1.0.0

    ...>  docker run -d -p 8080:8080 -v "$(PWD):/ponchiq" nikpos0fficial/ponchiq:1.0.0  /* запуск с bind mounts (-v "$(PWD):/ponchiq" => появляется опция монтирования корневой папки образа), сервис успешно работает */
    dc165f3de811d951f68058872493b440bfe25657f1e8510edee7c83caa6bc15c

## Вывод ##

В рамках данной работы я успешно собрал образ в Dockerfile для собственного веб - проекта с учётом .dockerignore, указал все зависимости, отправил образ на удалённый сервер на Docker Hub, зате успешно запустил образ, взяв его с удаленного сервера. Кроме того, проверил работоспособность при запуске с Bind Mounts.

Я удовлетворен проделанной работой, так как данная работа является моим первым опытом контейнеризации конкретных проектов, причём успешным. Тем не менее, первоначально были некоторые неполадки в работе образа - при запуске с Bind Mount сайт не работал, решилось методом тыка путём изменения текстовой кодировки app.py с UTF-16 на UTF-8. Но сейчас с уверенностью могу сказать, что освоил технологию контейнеризации через Docker.