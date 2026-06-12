# sdd-design

Atualiza ou cria componentes do design-system seguindo os tokens e padrões do
projeto. Use para adicionar componentes visuais, ajustar o tema, ou preparar
o projeto para edição no Onlook.

## Quando usar
- Adicionar um componente novo (botão, card, badge, modal…)
- Ajustar tokens de cor, tipografia ou espaçamento
- Preparar componentes para edição no Onlook (verificar compatibilidade de AST)
- Criar ou atualizar uma story no Storybook
- Revisar consistência visual entre telas

## O que o skill faz

### 1. Entende o contexto
- Lê `app/globals.css` para ver os tokens disponíveis.
- Lê `tailwind.config.ts` para ver o mapeamento de variáveis.
- Lista `components/` para entender o que já existe.

### 2. Implementa
- Cria ou edita o componente em `components/<nome>.tsx`.
  - Usa `cn()` para merging de classes.
  - Usa só tokens (`bg-primary`, `text-foreground`, etc.) — sem hardcode de cor.
  - Estrutura Onlook-compatible: JSX direto, sem HOC dinâmico.
- Cria a story em `components/<nome>.stories.tsx` com:
  - Variante padrão.
  - Variantes de estado (hover, disabled, error) quando aplicável.
  - Decorator com `ThemeProvider` se o componente usa tema.
- Cria o teste em `components/<nome>.test.tsx` (Vitest + RTL, 100% branches).

### 3. Valida
```bash
npm run build          # next build limpo
npm run storybook:build  # storybook build limpo
npm run test           # vitest 100% coverage
npx biome check app components lib  # lint limpo
```

## Onlook — como usar no projeto

O Onlook é um editor visual WYSIWYG para Next.js + Tailwind que **escreve de volta
no código via AST**. Instale em: https://onlook.dev

```bash
# 1. Inicie o dev server do projeto
npm run dev

# 2. Abra o Onlook e aponte para localhost:3000
#    O Onlook detecta componentes via instrumentação do Babel

# 3. Edite visualmente — as mudanças aparecem nos arquivos .tsx em tempo real
```

**Requisitos para compatibilidade com Onlook:**
- `className` deve ser uma string literal ou `cn(...)` — não template literal com
  expressão complexa.
- Componentes devem ter JSX no return do componente, não em variáveis separadas.
- Não use `forwardRef` onde não é necessário.
