# API de Atividades da Mergington High School

Uma aplicação FastAPI super simples que permite aos alunos visualizar e se inscrever em atividades extracurriculares.

## Funcionalidades

- Visualizar todas as atividades extracurriculares disponíveis
- Inscrever-se em atividades
- Exibir anúncios dentro do período de validade
- Gerenciar anúncios com uma sessão autenticada de professor

## Como começar

1. Instale as dependências:

   ```
   pip install fastapi uvicorn
   ```

2. Execute a aplicação:

   ```
   python app.py
   ```

3. Abra seu navegador e acesse:
   - Documentação da API: http://localhost:8000/docs
   - Documentação alternativa: http://localhost:8000/redoc

## Endpoints da API

| Método | Endpoint | Descrição |
| ------ | -------- | --------- |
| GET | `/activities` | Obtém atividades; aceita filtros opcionais `day`, `start_time` e `end_time`. |
| GET | `/activities/days` | Lista os dias com atividades. |
| POST | `/activities/{activity_name}/signup?email=...&teacher_username=...` | Inscreve um estudante; requer `teacher_username` válido. |
| POST | `/activities/{activity_name}/unregister?email=...&teacher_username=...` | Remove um estudante; requer `teacher_username` válido. |
| POST | `/auth/login?username=...&password=...` | Autentica um professor e retorna `session_token`. |
| GET | `/auth/check-session` | Valida a sessão enviada no cabeçalho Bearer. |
| POST | `/auth/logout` | Revoga a sessão enviada no cabeçalho Bearer. |
| GET | `/announcements/active` | Lista anúncios cuja data de início e expiração permitem exibição. |
| GET | `/announcements/manage` | Lista todos os anúncios; requer sessão autenticada. |
| POST | `/announcements` | Cria um anúncio; requer sessão autenticada. |
| PUT | `/announcements/{announcement_id}` | Atualiza um anúncio; requer sessão autenticada. |
| DELETE | `/announcements/{announcement_id}` | Exclui um anúncio; requer sessão autenticada. |

Envie `session_token` no cabeçalho `Authorization: Bearer <session_token>` para `/auth/check-session`, `/auth/logout` e rotas de gerenciamento de anúncios. As sessões expiram após 12 horas. Cada anúncio possui `message` e `expires_at` obrigatórios e `starts_at` opcional, todos enviados como JSON; as datas usam o formato `YYYY-MM-DD`.

Corpo JSON para criar ou atualizar um anúncio:

```json
{
   "message": "Inscrições abertas até sexta-feira.",
   "starts_at": null,
   "expires_at": "2026-12-31"
}
```

## Modelo de Dados

A aplicação usa um modelo de dados simples com identificadores significativos:

1. **Atividades** - Usa o nome da atividade como identificador:
   - Descrição
   - Horário
   - Número máximo de participantes permitidos
   - Lista de e-mails dos alunos inscritos

2. **Anúncios** - Armazenados no MongoDB com mensagem, data de expiração obrigatória e data de início opcional.

O banco MongoDB é inicializado com atividades, contas de professores e um anúncio de exemplo quando as respectivas coleções estão vazias.
