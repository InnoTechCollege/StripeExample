<template>
  <!-- Very simple page that shows a failure message, no JS or style here just HTML -->
  <div class="grid-center">
    <v-card id="failure-card" max-width="344">
      <v-img
        src="https://media1.giphy.com/media/d2W7eZX5z62ziqdi/giphy.gif"
        height="200px"
      ></v-img>

      <v-card-title> Payment Failed </v-card-title>

      <v-card-subtitle>Failure young grasshopper </v-card-subtitle>

      <v-card-actions>
        <v-btn @click="$router.push('/')"> Get Back! </v-btn>

        <v-spacer></v-spacer>

        <v-btn icon @click="show = !show">
          <v-icon>{{ show ? "mdi-chevron-up" : "mdi-chevron-down" }}</v-icon>
        </v-btn>
      </v-card-actions>

      <v-expand-transition>
        <div v-show="show">
          <v-divider></v-divider>

          <v-card-text>
            They're using our own satellites against us. And the clock is
            ticking. I was part of something special. You really think you can
            fly that thing? This thing comes fully loaded. AM/FM radio,
            reclining bucket seats, and... power windows. I was part of
            something special.
          </v-card-text>
        </div>
      </v-expand-transition>
    </v-card>
  </div>
</template>

<script>
export default {
  data() {
    return {
      show: false,
    };
  },
};
</script>

<style scoped>
</style>