# sdd-design

Atualiza ou cria componentes do design-system seguindo os tokens e padrões do
projeto. Use para adicionar componentes visuais ou ajustar o tema.

## Quando usar
- Adicionar um componente novo (botão, card, badge, modal…)
- Ajustar tokens de cor, tipografia ou espaçamento
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
