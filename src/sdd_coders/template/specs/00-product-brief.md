# Product Brief — {{ project_name }}

> **Como preencher.** Este documento é o resultado da **entrevista inicial**
> (`/sdd-interview`). Responda em **português**, com foco no **negócio e nas dores**
> — não em tecnologia (a arquitetura já está decidida na `constitution.md`).
> Cada seção traz as perguntas que o agente entrevistador fará. Deixe `TODO` no
> que ainda não souber; o agente ajuda a refinar.

---

## 1. Visão em uma frase

_Qual é o produto, para quem, e qual transformação ele gera?_

> TODO

## 2. Problema & dores

_Quais dores reais existem hoje? Como as pessoas resolvem isso atualmente? Qual o
custo de não resolver?_

- Dor principal: TODO
- Dores secundárias: TODO
- Como é resolvido hoje (workaround): TODO

## 3. Usuários & personas

_Quem usa? Quais papéis existem (ex.: cliente final, operador, **admin**)? Qual o
nível de conhecimento técnico?_

| Persona | Objetivo | Papel/permissões |
| --- | --- | --- |
| TODO | TODO | TODO |

## 4. Jobs-to-be-done

_Quais tarefas o usuário precisa concluir? ("Quando ___, quero ___, para ___.")_

- TODO

## 5. Escopo

**Dentro do MVP:**
- TODO

**Fora do MVP (por enquanto):**
- TODO

## 6. Páginas / telas

_Liste as telas previstas e o propósito de cada uma. (Isto vira a navegação.)_

| Página | Propósito | Quem acessa |
| --- | --- | --- |
| `/login` | Autenticação | Público |
| `/` (dashboard) | Visão principal | Autenticado |
| `/admin` | Administração | Admin |
| TODO | TODO | TODO |

## 7. Funcionalidades principais

_Liste as funcionalidades em ordem de prioridade. Cada uma vira uma spec funcional
(`functional/<feature>.md`)._

1. TODO
2. TODO

## 8. Regras de negócio

_Restrições, cálculos, validações e fluxos que o sistema deve respeitar._

- TODO

## 9. Dados & entidades

_Quais entidades existem e como se relacionam? Quais dados são **pessoais (PII)**?_

- Entidades: TODO
- PII a proteger (LGPD): TODO

## 10. Integrações externas

_Pagamentos, e-mail, storage, APIs de terceiros, etc._

- TODO

## 11. Requisitos não-funcionais específicos

_Volume esperado, latência, picos, multi-tenant?, idiomas, acessibilidade._

> Os NFRs padrão (segurança, RLS, observabilidade, 100% de testes) já vêm da
> constituição. Aqui registre apenas o que é **específico deste produto**.

- TODO

## 12. Compliance & privacidade

_Além da LGPD (default), há requisitos setoriais (saúde, financeiro, etc.)?_

- TODO

## 13. Métricas de sucesso

_Como saberemos que está funcionando? (ativação, retenção, conversão, NPS…)_

- TODO

## 14. Riscos & premissas

- Premissas: TODO
- Riscos: TODO
