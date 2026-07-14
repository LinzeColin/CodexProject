import { lazy } from "react";



export const GalaxyScene = lazy(() => import("../../components/GalaxyScene").then((module) => ({ default: module.GalaxyScene })));


export const ObsidianGraphScene = lazy(() => import("../../components/ObsidianGraphScene").then((module) => ({ default: module.ObsidianGraphScene })));
