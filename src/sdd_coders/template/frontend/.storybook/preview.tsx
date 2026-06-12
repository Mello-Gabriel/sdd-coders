import type { Preview } from "@storybook/react-vite";
import "../app/globals.css";

const preview: Preview = {
  parameters: {
    backgrounds: {
      default: "light",
      values: [
        { name: "light", value: "hsl(0 0% 100%)" },
        { name: "dark", value: "hsl(222.2 84% 4.9%)" },
      ],
    },
  },
};

export default preview;
