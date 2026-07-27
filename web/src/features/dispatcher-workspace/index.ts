/**
 * Public surface of the dispatcher-workspace feature.
 */
export { DispatcherWorkspacePage } from "./pages";
export { DispatcherWorkspace } from "./components";
export * as dispatcherApi from "./api";
export { useDispatcherStore } from "./store/dispatcher.store";
export { dispatcherSocket } from "./services";
export * from "./types";
