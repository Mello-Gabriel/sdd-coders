# Constituição do Projeto

> **Rascunho gerado por `sdd-coders adopt`.** Este arquivo ainda **não** descreve
> o seu projeto — ele é um esqueleto com lacunas marcadas como `TODO`.
> Rode **`/sdd-constitution`** e responda às perguntas: o agente lê o repositório
> (linguagens, gerenciadores de pacote, CI, testes) e preenche isto com você.
>
> **O que é este documento.** A _constituição_ define a arquitetura, os padrões e
> os princípios **inegociáveis** do projeto. Toda decisão dos agentes é
> restringida por ela. As decisões _funcionais_ (o que o produto faz) ficam nas
> specs funcionais (`specs/functional/`), não aqui.
>
> Mudanças aqui exigem um **ADR** (`docs/adr/NNNN-titulo.md`) registrando
> contexto, decisão, alternativas e consequências.

Idioma: **TODO** — defina o idioma de specs/princípios e o de código, API,
identificadores e mensagens de commit.

---

## 1. Princípios inegociáveis (NON-NEGOTIABLE)

> Poucos e reais. Um princípio que você não faria valer num PR não é um
> princípio — é uma boa intenção. Comece com 3 a 5.

1. **Spec-first.** Nenhuma feature é implementada sem uma spec funcional
   aprovada em `specs/functional/`.
2. **TODO** — ex.: seguro por padrão (_deny by default_), tipagem estrita,
   piso de cobertura de testes, observabilidade obrigatória, simplicidade.
3. **TODO**

---

## 2. Stack (o que já existe)

> Descreva o stack **real** do repositório, não o desejado. Se algo está em
> migração, registre os dois lados e o destino.

| Camada | Tecnologia |
| --- | --- |
| Linguagem(ns) | TODO |
| Framework(s) | TODO |
| Gerenciador de pacotes | TODO |
| Banco de dados / persistência | TODO |
| Testes | TODO |
| Lint / format | TODO |
| Type checking | TODO |
| Build / empacotamento | TODO |
| CI/CD | TODO |
| Deploy / runtime | TODO |

Trocar qualquer item desta tabela é uma decisão de **constituição** → requer ADR.

---

## 3. Padrões de qualidade

- **Testes:** TODO — o que é obrigatório (unit/integração/E2E) e qual o piso de
  cobertura, se houver gate no CI.
- **Lint/Format:** TODO — comandos exatos e se o CI falha em violação.
- **Tipos:** TODO — checker, nível de rigor, política sobre supressões.
- **Convenções de nomes:** TODO.

### Comando do quality gate

O `/sdd-verify` roda este comando; ele precisa existir e ser confiável:

```bash
# TODO: substitua pelo gate real do projeto
# ex.: make check   |   npm run ci   |   uv run pytest && uv run ruff check
```

---

## 4. Segurança

- **TODO** — linha de base (ex.: OWASP Top 10), validação de entrada, autorização.
- **Segredos** nunca no repositório. TODO: onde vivem e como o CI os verifica.
- **TODO** — headers, rate limiting, dependências monitoradas.

---

## 5. Arquitetura & fronteiras

> Onde mora cada coisa e o que **não** pode depender de quê. É a seção que mais
> evita que os agentes façam bagunça num repo grande.

- Módulos/pacotes principais e sua responsabilidade: TODO.
- Regras de dependência (ex.: "domínio não importa infraestrutura"): TODO.
- Pontos de extensão e onde código novo deve nascer: TODO.

---

## 6. Documentação

- TODO — o que é gerado (API, referência, changelog) e o que é escrito à mão.
- TODO — onde é publicado e se o CI valida.

---

## 7. Git, CI/CD

- Fluxo: TODO (PRs, branch protection, quem aprova).
- Mensagens de commit: TODO (ex.: Conventional Commits).
- O que o CI roda em todo push/PR: TODO.

---

## 8. Processo SDD & agentes

Pipeline (ver `.claude/skills/sdd-*`):

`/sdd-specify` → `/sdd-plan` → `/sdd-tasks` → `/sdd-implement` → `/sdd-verify`
→ `/sdd-docs`.

- As **specs funcionais** usam **notação EARS** (ver `specs/functional/_template.md`).
- Um **orquestrador** delega a subagentes especializados. Cada agente respeita
  esta constituição.
- Em projetos adotados, `/sdd-interview` é opcional: o produto já existe. Comece
  por `/sdd-constitution` e depois `/sdd-specify` para a próxima feature.

### Notação EARS (resumo)

| Padrão | Forma |
| --- | --- |
| Ubíquo | "O `<sistema>` **deve** `<comportamento>`." |
| Estado | "**Enquanto** `<estado>`, o `<sistema>` **deve** `<comportamento>`." |
| Evento | "**Quando** `<gatilho>`, o `<sistema>` **deve** `<comportamento>`." |
| Opcional | "**Onde** `<feature presente>`, o `<sistema>` **deve** `<comportamento>`." |
| Indesejado | "**Se** `<gatilho>`, **então** o `<sistema>` **deve** `<comportamento>`." |

---

## 9. Como evoluir a constituição

Qualquer mudança aqui requer um **ADR** em `docs/adr/NNNN-titulo.md` descrevendo:
contexto, decisão, alternativas consideradas e consequências. A constituição é
estável **por design** — projetos divergem nas specs funcionais, não na
arquitetura.
