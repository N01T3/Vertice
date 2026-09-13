declare module "*.vue" {
  import type { DefineComponent } from "vue";
  const componente: DefineComponent<Record<string, unknown>, Record<string, unknown>, unknown>;
  export default componente;
}
