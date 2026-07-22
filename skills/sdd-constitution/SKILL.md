---
name: sdd-constitution
description: Create or update specs/constitution.md — the project's fixed architecture, quality gate and non-negotiable principles. Run first in a repository adopted with `sdd-coders adopt`; in a scaffolded project only to make a deliberate, ADR-backed change.
---

# /sdd-constitution

Preenche ou revisa a **constituição** do projeto: o documento que restringe toda
decisão dos agentes. Tudo o mais no pipeline depende dele — uma constituição com
`TODO` faz `/sdd-plan` e `/sdd-verify` inventarem regras.

## Quando usar

- **Repo adotado** (`sdd-coders adopt`): é o **primeiro** passo. A
  `specs/constitution.md` vem como esqueleto com `TODO`.
- **Projeto gerado** (`sdd-coders init`): a constituição já vem decidida pelo
  modelo base. Só rode aqui para uma mudança **deliberada** — e ela exige ADR.

## Como agir

1. **Leia antes de perguntar.** Não peça ao usuário o que o repositório já diz.
   Levante do próprio código:
   - linguagens e versões; manifestos (`pyproject.toml`, `package.json`,
     `go.mod`, `Cargo.toml`, `pom.xml`, …) e o gerenciador de pacotes real
     (procure o lockfile);
   - framework(s) e camada de persistência;
   - runner de testes, configuração de cobertura e se há gate;
   - lint/format e type checker configurados;
   - o que o CI roda (`.github/workflows/*`, `.gitlab-ci.yml`, `Makefile`);
   - como o projeto é empacotado e onde roda em produção.
2. **Apresente o que você inferiu** como uma lista de fatos, marcando o que está
   incerto. Peça confirmação, não redigitação.
3. **Pergunte só o que o código não responde** — no máximo 5 por vez:
   - Quais princípios você faria valer **bloqueando um PR**? (3 a 5, reais.)
   - Qual é o **comando exato do quality gate** que `/sdd-verify` deve rodar?
   - Que fronteiras de arquitetura não podem ser violadas (quem não importa quem)?
   - Idioma de specs vs. idioma de código/commits.
   - Algo em migração, com dois lados válidos hoje?
4. **Escreva `specs/constitution.md`** sem deixar nenhum `TODO`. Se uma seção
   não se aplica, diga isso explicitamente ("Não se aplica: este projeto não
   expõe API HTTP") em vez de apagá-la.
5. **Verifique o gate.** Rode o comando declarado na seção "Comando do quality
   gate". Se ele falhar ou não existir, corrija a constituição — um gate que não
   roda é pior que nenhum, porque `/sdd-verify` vai confiar nele.
6. **Se estiver alterando uma constituição existente**, escreva também o ADR em
   `docs/adr/NNNN-titulo.md` (contexto, decisão, alternativas, consequências) e
   mostre o diff ao usuário antes de gravar.

## Regras

- A constituição descreve o stack que **existe**, não o desejado. Aspiração vai
  para um ADR de migração, não para a tabela de stack.
- Nada de princípio decorativo. Se ninguém barraria um PR por causa dele, corte.
- Decisão **funcional** (o que o produto faz) não entra aqui — vai para
  `specs/functional/`.

## Saída

- `specs/constitution.md` preenchido, sem `TODO`, com o comando do gate validado.
- (Se for alteração) `docs/adr/NNNN-titulo.md`.
- Próximo passo: **`/sdd-specify`**.
