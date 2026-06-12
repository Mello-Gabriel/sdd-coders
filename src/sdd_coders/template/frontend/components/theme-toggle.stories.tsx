import type { Meta, StoryObj } from "@storybook/react-vite";
import { ThemeToggle } from "./theme-toggle";

const meta: Meta<typeof ThemeToggle> = {
  component: ThemeToggle,
  parameters: {
    nextjs: { appDirectory: true },
  },
};
export default meta;
type Story = StoryObj<typeof ThemeToggle>;

export const Default: Story = {};
