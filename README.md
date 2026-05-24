## Execução do Projeto

Este projeto adota uma arquitetura unificada em *monorepo* com orquestração via Docker. Os passos a seguir orientam a preparação do ambiente de execução.

### Pré-requisitos

- **Docker** e **Docker Compose** instalados no ambiente de destino.
- **Arquivo `.env`: O arquivo `.env` oficial (disponibilizado por e-mail à instituição) é obrigatório**. Sem ele, o sistema não disporá das chaves necessárias para configurar os serviços de banco de dados, mensageria e autenticação.

### Passo a Passo

1. **Clonar o repositório**

  ```bash
   git clone https://github.com/marciodelfinooliveira/RentaiAppUFPB.git
  ```

2. **Configurar o ambiente**

- **Copie o arquivo .env (recebido por e-mail) para o diretório raiz rentai/**.

- Verifique se o arquivo está nomeado exatamente como .env.

3. **Subir a infraestrutura**

- Execute o comando abaixo na raiz do projeto para construir as imagens e iniciar todos os serviços (API, front-end, PostgreSQL, Redis, Kafka e Nginx Gateway):


   ```bash
  docker compose up -d --build
  ```

3. **Acessar o sistema**

- **Aplicação: https://localhost (navegador)**

- **Documentação da API: https://localhost/docs (para visualizar contratos e testar endpoints)**

- ### **Aviso Importante: O arquivo .env é indispensável. Caso não esteja presente na raiz do projeto, o orquestrador falhará ao configurar serviços essenciais como Kafka e PostgreSQL. Verifique se o arquivo contém todas as variáveis de ambiente necessárias antes de executar o comando de build.**

### Eventuais comandos de manutenção

| Comando | Descrição |
|---------|-----------|
| `docker compose stop` | Interrompe a execução do sistema. |
| `docker compose down` | Para todos os containers, mantendo os volumes. |
| `docker compose up -d` | Reinicia o sistema em segundo plano. |
| `docker compose logs -f [nome_do_servico]` | Exibe logs em tempo real. de um serviço específico. |
| `docker compose down -v` | Remove containers **e volumes** de dados. |

## Documentação e Contrato de API

Para assegurar o alinhamento entre a implementação e os requisitos de negócio, foi adotado a abordagem *spec-driven*. Todo o contrato da API foi formalizado por meio do padrão OpenAPI/Swagger conjuntamente à codificação dos *endpoints*. Essa prática garantiu a consistência entre os esquemas de dados esperados pelo *front-end* e aqueles efetivamente entregues pelo *back-end*, permitindo que quaisquer alterações nos contratos de interface sejam rastreáveis e validadas em etapas precoces do desenvolvimento.

- **É possível explorar interativamente os contratos, testar os esquemas de dados e validar os critérios de aceite de cada funcionalidade acessando a documentação local no link abaixo, DESDE QUE OS CONTAINERS ESTEJAM DE PÉ:**

- **https://localhost/docs**

Esta documentação é gerada automaticamente pelo FastAPI, assegurando que o contrato exibido seja sempre uma representação fiel da implementação vigente.

## Ferramentas de IA utilizadas

Durante o desenvolvimento, a ferramenta de inteligência artificial atuou como suporte e acelerador do processo, optei pela utilização do **Gemini** como agente de aceleração do desenvolvimento ágil de funcionalidades, empregando-o como consultor para análise de logs, depuração de conflitos e configuração de proxy entre os serviços.

### Dinâmica de Trabalho

A IA foi orientada por meio de *Context-Aware Prompting*, no qual foram fornecidos logs de erro e estruturas de arquivos existentes previamente a qualquer sugestão de alteração, essa abordagem garantiu a compreensão técnica do contexto do problema, bem como a compreensão das limitações impostas pelos serviços isolados antes da proposição de qualquer modificação.

### Avaliação geral

A IA demonstrou utilidade na resolução de problemas desde que o contexto e as limitações de sua atuação fossem claramente explicitados a fim de evitar alucinações e respostas desconexas ou que trariam atraso no desenvolvimento. Em diversas ocasiões, ela acelerou o desenvolvimento mediante análise criteriosa dos logs de erro, conseguindo identificar com boa precisão os pontos que demandavam ajustes. Como principal destaque do meu ponto de vista foi no desenvolvimento do *frontend*, área na qual ainda cometo mais erros. O suporte do Gemini foi essencial para orientar a condução da evolução do app em Vue.Js, em situações de conflitos de integração com a API, com o proxy e com o WebSocket, além de auxiliar na identificação de sintaxes incorretas causadoras de erros no JavaScript e na análise dos logs do console. Diante disso, considero sua contribuição determinante para a entrega dentro do prazo estipulado, dada a amplitude do escopo do projeto.

## Limitações Conhecidas e Preparação para Produção

#### O sistema foi arquitetado seguindo padrões de alta disponibilidade, segurança e escalabilidade, garantindo que a transição do ambiente de desenvolvimento para a produção seja um processo de implantação trivial, sem necessidade de refatoração estrutural.

### O que diferencia este ambiente de um de produção ?

| Aspecto | Ambiente de Desenvolvimento | Ambiente de Produção |
|---------|----------------------------|----------------------|
| **Gestão de Certificados SSL/TLS** | Certificados autoassinados gerados automaticamente pelo container `cert-generator`, permitindo tráfego HTTPS em ambiente local. | Substituição por autoridades certificadoras reconhecidas (ex.: Let's Encrypt com Certbot), mantendo a mesma estrutura de volumes consumida pelo Nginx. |

### Conclusão

O sistema encontra-se em um estado de maturidade avançado, a lógica de negócio, o desacoplamento via mensageria, a estratégia de *reverse proxy* e a consistência do modelo de dados por meio de SQLAlchemy/Alembic já conseguem ser suficientes para o que se espera de uma aplicação de nível corporativo.

A transição para um servidor de produção resume-se, portanto, a uma mudança na infraestrutura externa (certificados validados), mantendo a camada de aplicação intacta e plenamente funcional.

## Testando o Fluxo de Teleconsultoria

Este guia tem por objetivo validar a integração completa entre o *front-end*, a API, o Redis, o banco de dados e a mensageria via Kafka.

### Pré-requisitos

- Sistema em execução (`docker compose up -d`)
- Acesso ao Mailhog para validação de recebimento de e-mails em: **http://localhost:8025**

### Passo a Passo do Fluxo Completo

#### 1. Registro de Usuário

| Etapa | Procedimento | Validação |
|-------|--------------|-----------|
| Acesso | Acesse a aplicação em **https://localhost** | — |
| **Cadastro do Médico APS** | Preencha o formulário de cadastro para um **médico APS** | — |
| Processamento | Acesse **http://localhost:8025** (Mailhog) | Verifique se o *token* de confirmação foi recebido |
| Confirmação | Insira o *token* no campo e confirme | Insira o *token* no campo e finalize o cadastro de um **médico APS** |
| **Cadastro do Médico Especialista** | **Em outro navegador, ou em aba anônima, cadastre um novo usuário** |
| Cadastro | Preencha o formulário de cadastro para um **médico Especialista** | — |
| Processamento | Acesse **http://localhost:8025** (Mailhog) | Verifique se o *token* de confirmação foi recebido |
| Confirmação | Insira o *token* no campo e confirme | Insira o *token* no campo e finalize o cadastro de um **médico Especialista** |

#### 2. Autenticação e Sessão

| Etapa | Procedimento | Validação |
|-------|--------------|-----------|
| Login | Utilize as credenciais criadas para realizar o login no **médico APS** | O sistema deve gerar o JWT e armazená-lo. Verifique no console do navegador se a requisição `/api/login` retornou o status `200` |
| Login | Utilize as credenciais criadas para realizar o login no **médico Especialista** | O sistema deve gerar o JWT e armazená-lo. Verifique no console do navegador se a requisição `/api/login` retornou o status `200` |
---

#### 3. Cadastro de Paciente

| Etapa | Procedimento | Validação |
|-------|--------------|-----------|
| Cadastro | **Com um Médico APS** navegue até a área de pacientes e realize o cadastro do paciente, incluindo ou não arquivos de prontuário | O sistema deve confirmar o sucesso do cadastro e o paciente deve estar listado na base |

---

#### 4. Agendamento da Teleconsultoria

| Etapa | Procedimento | Validação |
|-------|--------------|-----------|
| Agendamento | **Com um Médico APS** navegue até a área de agendamento e selecione um horário disponível, insira as informações do paciente e realize o cadastro | Verifique se o registro foi persistido observando a tela de detalhes da Teleconsulta |
---

#### 5. Processamento de Notificação

| Etapa | Procedimento | Validação |
|-------|--------------|-----------|
| Disparo | Após confirmar o agendamento, o sistema disparará um evento assíncrono | **Se você estiver logado em ambos os médicos em navegadores separados**, conseguirá ver a solicitação de teleconsultoria chegando para o **Médico Especialista**, e caso este o abra, conseguirá ver na tela do **Médico APS** a teleconsultoria mudando de status conforme o **Médico Especialista** a analisa em tempo real.|
---

#### 6. Validação de Segurança (Blacklist)

| Etapa | Procedimento | Validação |
|-------|--------------|-----------|
| Logout | Realize o logout | — |
| Validação | Tente acessar uma rota protegida (ex.: `/api/teleconsultas/me`) usando o *token* antigo | O sistema deve retornar `401 Unauthorized`, confirmando que o *token* foi invalidado no Redis |
---

## 3. Configuração e Extensibilidade do Serviço de Validação de IA

O sistema de validação de arquivos (prontuários e documentos de teleconsultas) foi concebido com base nos princípios de **Injeção de Dependência** e **Desacoplamento**, permitindo que o motor de análise de confiança (IA) seja substituído ou reconfigurado sem a necessidade de alteração das regras de negócio da aplicação.

### Como substituir o serviço de IA

#### Interface de Serviço

A lógica de validação encontra-se em `app/services/ai_validation_service.py`. Para substituir a simulação da IA responsável pelo processamento dos arquivos, deve-se implementar uma nova classe que siga o mesmo contrato (*interface*), ou seja, que receba o arquivo como entrada e retorne um *score* de confiança (*confidence score*) e uma decisão booleana sobre a conformidade do conteúdo analisado.

#### Configuração via `.env`

Os parâmetros operacionais para o processamento desses arquivos, como `AI_CONFIDENCE_THRESHOLD`, são injetados por meio de variável de ambiente e caso haja troca do provedor de IA, basta ajustar o novo *endpoint* ou a chave de API no arquivo `.env` localizado na raiz do projeto.

#### Substituição do Motor

| Passo | Procedimento |
|-------|--------------|
| 1 | Implemente o novo conector responsável pela leitura e análise dos arquivos no módulo de serviços |
| 2 | Atualize a instância do serviço no *container* da API |
| 3 | Reinicie o *container* com o comando `docker compose restart api` |


Esta arquitetura permite que, em um cenário futuro, seja possível substituir um serviço de IA proprietário por um modelo de código aberto executado localmente capaz de realizar a análise de arquivos. Tal alteração afetaria apenas a camada de integração do serviço, enquanto o fluxo de agendamento e a interface do médico permaneceriam inalterados.


## Arquitetura

O sistema foi concebido para ser resiliente, escalável e de fácil manutenção, seguindo os princípios de *Clean Code* e *Clean Architecture*. A seguir, detalham-se as escolhas fundamentais que sustentam a solução proposta.

### 1. Núcleo da API: FastAPI (Async) e SQLAlchemy com Alembic

- **FastAPI (Async)**: A framework foi selecionada devido à sua performance nativa superior em requisições *I/O bound* e à facilidade de implementação de rotas assíncronas, garantindo que o sistema atenda a múltiplos usuários com baixa latência.

- **SQLAlchemy + Alembic**: O Alembic foi adotado para assegurar o versionamento do banco de dados (*schema migrations*) como código, permitindo que a evolução da estrutura da base de dados seja rastreável e segura em diferentes ambientes, enquanto o SQLAlchemy provê uma camada de abstração eficiente que permite a construção de consultas de forma legível e performática.

### 2. Mensageria e Cache: Kafka e Redis

- **Kafka**: Adotado para o desacoplamento entre serviços, utiliza-se o Kafka no processamento do fluxo de eventos como o envio de *tokens* de confirmação de e-mail, essa abordagem garante que, mesmo que o serviço de e-mail esteja sob alta carga ou temporariamente indisponível, o registro do usuário seja processado sem falhas, assegurando durabilidade.

- **Redis**: Implementado tanto como *cache* para performance quanto para o gerenciamento de *blacklist* de JWT (*JSON Web Tokens*), essa estratégia possibilita a revogação instantânea de *tokens* de autenticação, oferecendo uma camada adicional de segurança apenas com JWT *stateless*.

### 3. Abordagem: Reuso Estratégico de Conhecimento

- **A arquitetura reflete uma estrutura de diretórios consolidada (`core`, `schemas`, `db`, `endpoints`, `services`), que prioriza a separação de responsabilidades**, onde a decisão de manter essa estrutura, em vez de refatorar para novos padrões, baseou-se em evidências de robustez prévia.

- **Trade-off**: Optou-se por manter o padrão já validado por mim em projetos de estudo anteriores, reduzindo drasticamente o risco de erros de implementação em uma janela de tempo curta, além de já me dar uma ótima base para iniciar o projeto.

- **Vantagem**: A quem observar e testar o código, encontrará um código previsível e estruturado, no qual cada componente desempenha uma função clara, reduzindo a carga cognitiva necessária para novas implementações.

### 4. Orquestração e Infraestrutura: Nginx Gateway e Monorepo

- **Arquitetura com Nginx Gateway**: Adotou-se um Nginx centralizado como *reverse proxy* para gerenciar HTTPS e distribuir o tráfego entre a API e o *front-end*, essa abordagem centraliza a segurança e elimina a necessidade de expor múltiplos *containers* diretamente à internet.

- **Monorepo**: A unificação dos repositórios (API e o Frontend) por meio de um arquivo `docker-compose.yml` raiz permite uma orquestração global, resolveu-se o desafio da comunicação entre serviços sem a complexidade de gerenciar múltiplas redes externas, além de tornar mais prático ao avaliador a execução do projeto a partir de um único repositório.

### 5. Camada de Apresentação: Vue.js e Servidor de Arquivos Estáticos

- **Vue.js**: A escolha do framework baseia-se em sua reatividade performática e no ecossistema de componentes modularizados, o que permite o desenvolvimento de uma interface de usuário (*UI*) dinâmica e fluida. A decisão pela ferramenta visa o desacoplamento total entre a lógica de apresentação e o *back-end*, permitindo que o *front-end* atue como um cliente independente que consome a API por meio de requisições assíncronas.

- **Servidor de Arquivos Estáticos (Nginx em Container Isolado)**: O *front-end* é servido por um container dedicado, cuja única função é a entrega eficiente de artefatos estáticos compilados (HTML, JavaScript e CSS). Ao isolar o Vue.js em seu próprio ambiente, asseguramos que o ciclo de vida do *front-end* (processos de *build* e entrega) seja completamente independente da API. O container do *front-end* não expõe portas externas, ele se comunica exclusivamente com o Nginx Gateway, que realiza o roteamento reverso (`/` direcionado ao *front-end* e `/api` direcionado ao *back-end*). Essa segregação em containers isolados promove uma arquitetura baseada no princípio do **menor privilégio**, na qual o servidor de arquivos não possui conhecimento da lógica de negócio nem das rotas da API. Como resultado, reduz-se a superfície de ataque e otimiza-se a entrega dos ativos estáticos.


### Fluxograma das Arquiteturas 
```bash
Browser
   │  HTTPS (80→443) + WebSocket
   ▼
nginx (raiz) ──► API FastAPI (:8000)     ──► PostgreSQL
            └──► Frontend estático       ──► Redis (códigos, blacklist JWT, pub/sub)
                                           └──► Kafka
                                                  ├── email_consumer → MailHog
                                                  └── notif_consumer → Redis → API → WebSocket
```


#### Estrutura da Raiz

```bash
rentai/
│
├── APIRentai/                  # Backend FastAPI.
├── AppFrontRentai/             # Frontend VueJs 3.
├── nginx/
│   └── ssl/                    # Certificados TLS locais (gerados pelo cert-generator).
│       ├── localhost.pem
│       └── localhost-key.pem
│
├── docker-compose.yml          # Orquestra todos os serviços (api, front, db, redis, kafka, nginx, consumers…).
├── .env                        # Variáveis de ambiente.
└── README.md                   # Notas sobre o projeto.
```

#### Estrutura da API

```bash
APIRentai/
│
├── app/
│   ├── api/
│   │   ├── deps.py                         # Injeção de dependências (sessão DB, JWT, papéis).
│   │   └── v1/
│   │       ├── api.py                      # Agregador de todas as rotas.
│   │       └── endpoints/
│   │           ├── users.py                # Cadastro, login, verify, refresh, logout, /me, especialistas.
│   │           ├── institutions.py         # Listagem e CRUD.
│   │           ├── patients.py             # Pacientes.
│   │           ├── files.py                # Upload, download e soft delete de anexos.
│   │           ├── teleconsultations.py    # Solicitações de teleconsultoria.
│   │           ├── pareceres.py            # Parecer do especialista.
│   │           └── notifications.py        # WebSocket de notificações em tempo real.
│   │
│   ├── core/
│   │   ├── config.py                       # Settings centralizadas.
│   │   ├── security.py                     # Hash de senha e criação/validação de JWT.
│   │   └── logging_config.py               # Configuração do comportamento dos logs para o app e Kafka.
│   │
│   ├── db/
│   │   ├── base.py                         # Base declarativa SQLAlchemy.
│   │   ├── session.py                      # Engine e sessão assíncrona (asyncpg).
│   │   └── models/
│   │       ├── user.py                     # Usuários/médicos e papéis.
│   │       ├── institution.py              # Instituições de saúde.
│   │       ├── patient.py                  # Pacientes e vínculo médico–paciente.
│   │       ├── file.py                     # Arquivos clínicos por paciente.
│   │       ├── teleconsultation.py         # Teleconsultorias e status.
│   │       └── parecer.py                  # Pareceres.
│   │
│   ├── schemas/                            # Pydantic (request/response da API).
│   │   ├── token.py
│   │   ├── user.py
│   │   ├── institution.py
│   │   ├── patient.py
│   │   ├── file.py
│   │   ├── teleconsultation.py
│   │   └── parecer.py
│   │
│   ├── services/
│   │   ├── user_service.py                 # Lógica de usuário (busca, persistência).
│   │   ├── kafka_service.py                # Produtor Kafka (eventos assíncronos).
│   │   ├── redis_service.py                # Redis (códigos, blacklist, pub/sub).
│   │   ├── websocket_manager.py            # Gerenciador de conexões WebSocket.
│   │   └── document_validator.py           # Validação mock de documentos por IA (score simulado).
│   │
│   └── main.py                             # App FastAPI, CORS, lifespan (Kafka, admin seed, Redis→WS).
│
├── consumers/                              # Workers Kafka (processos separados no Compose).
│   ├── user_registration_consumer.py       # E-mail de verificação de cadastro.
│   └── teleconsultation_notification_consumer.py  # Eventos de parecer/teleconsultoria → Redis.
│
├── alembic/                                # Migrações de banco.
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── fca774b3b254_create_database_tables.py
│
├── nginx/
│   └── nginx.conf                          # Proxy reverso: /api → API, / → frontend, TLS, WebSocket.
│
├── logs/                                   # Logs em runtime (app, kafka).
│
├── alembic.ini                             # Configuração do Alembic.
├── Dockerfile                              # Imagem da API e dos consumers.
├── Dockerfile.certs                        # Gera certificados self-signed para nginx/ssl.
├── entrypoint.sh                           # Aguarda Postgres, `alembic upgrade head`, sobe Uvicorn.
├── requirements.txt                        # Dependências Python.
├── .gitignore

```


#### Estrutura do FrontEnd


```bash
│
├── src/
│   ├── api/
│   │   ├── client.js                       # Axios: base URL, interceptors (token, refresh 401).
│   │   └── index.js                        # Facades: users, institutions, patients, files, teleconsultations, pareceres.
│   │
│   ├── stores/                             
│   │   ├── auth.js                         # Sessão, usuário logado, papéis.
│   │   └── teleconsultations.js            # Estado das teleconsultorias no dashboard.
│   │
│   ├── router/
│   │   └── index.js                        # Rotas Vue + guards (auth, guest, roles).
│   │
│   ├── views/                              # Telas da aplicação.
│   │   ├── LoginView.vue
│   │   ├── RegisterView.vue
│   │   ├── VerifyView.vue                  # Código vindo do e-mail.
│   │   ├── DashboardView.vue               # Lista/filtros de teleconsultorias.
│   │   ├── PatientsView.vue
│   │   ├── TeleconsultationFormView.vue    # Nova teleconsultoria.
│   │   ├── TeleconsultationDetailView.vue  # Detalhe, timeline, export PDF.
│   │   ├── ParecerFormView.vue             # Registrar parecer.
│   │   ├── AdminInstitutionsView.vue       # Instituições.
│   │   ├── ProfileView.vue
│   │   └── ForbiddenView.vue
│   │
│   ├── components/
│   │   ├── AppLayout.vue                   # Layout shell (menu, header).
│   │   ├── StatusBadge.vue                 # Badge de status da teleconsultoria.
│   │   └── FileAiAuditTag.vue              # Tag de auditoria IA no upload.
│   │
│   ├── composables/
│   │   ├── useNotifications.js             # Toast/alertas na UI.
│   │   └── realtimeNotifications.js        # WebSocket + sincronização em tempo real.
│   │
│   ├── utils/                              # Helpers (validação CPF/CNPJ, erros API, PDF, filtros…).
│   │   ├── authStorage.js
│   │   ├── errors.js
│   │   ├── realtimeSync.js
│   │   ├── notifications.js
│   │   ├── aiDocumentValidation.js         # Integração com validação de documento.
│   │   ├── exportPdf.js
│   │   └── …                               # cpf, cnpj, format, files, validações de formulário.
│   │
│   ├── constants.js                        # Papéis, especialidades, status.
│   ├── env.js                              
│   ├── assets/main.css
│   ├── App.vue
│   └── main.js                             
│
├── public/
│   └── favicon.svg
│
├── nginx/
│   └── default.conf                        # try_files → index.html (container do front).
│
├── index.html
├── vite.config.js                          # Alias @, proxy /api → https://localhost.
├── package.json
├── Dockerfile                              # Build Vite + serve estático com nginx.
├── .env.example
├── .gitignore
```


## Diagramas C4: Visão Arquitetural

A arquitetura foi estruturada para garantir isolamento e alta disponibilidade, sendo documentada por meio do diagrama C4 abaixo.

<p align="center">
  <img src="imagens/Captura%20de%20tela%20de%202026-05-24%2017-19-52.png" alt="Texto alternativo">
</p>


### Interpretação Arquitetural

O Nginx destaca-se como ponto único de entrada (*gatekeeper*), responsável por proteger os serviços internos e centralizar o gerenciamento de tráfego. A API, por sua vez comunica-se com o Redis para fins de autenticação e otimização de desempenho, e com o Kafka para o desacoplamento de eventos assíncronos. Essa estratégia assegura que picos de demanda — como os decorrentes de cadastros simultâneos ou teleconsultas — não comprometam a disponibilidade do serviço principal.

O diagrama explicita visualmente a separação entre a rede de aplicação e a rede de mensageria, evidenciando o isolamento funcional dos componentes. Ademais, torna claro que o fluxo referente à API é distinto do fluxo destinado ao *frontend*, o que reforça a clareza da arquitetura proposta. Por fim, a representação didática evidencia o papel de cada ferramenta no ecossistema como um todo, demonstrando, de maneira estruturada, os componentes da infraestrutura e suas respectivas funções.

