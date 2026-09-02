import {ContainerProxy, configureOutbound} from "./sandbox";
import {handleRoute} from "./routes";

export {ContainerProxy};
export {RvwSandbox} from "./sandbox";

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    configureOutbound(env);
    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/healthz") return Response.json({version: env.RVW_VERSION, env: env.RVW_ENV});
    return await handleRoute(request, env);
  },
} satisfies ExportedHandler<Env>;
