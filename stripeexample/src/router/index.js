import Vue from "vue";
import VueRouter from "vue-router";
import Home from "../views/Home.vue";
import Failure from "../views/Failure.vue";
import Success from "../views/Success.vue";

Vue.use(VueRouter);

const routes = [
  {
    path: "/",
    name: "Home",
    component: Home
  },
  {
    path: "/success",
    name: "Success",
    component: Success
  },
  {
    path: "/failure",
    name: "Fail",
    component: Failure
  },
];

const router = new VueRouter({
  routes
});

export default router;
