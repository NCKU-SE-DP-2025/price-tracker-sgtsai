<template>
  <nav class="navbar">
    <div class="title">
      <RouterLink to="/overview">價格追蹤小幫手</RouterLink>
    </div>

    <div class="hamburger" @click="toggleMenu">
      <i class="bi bi-list"></i>
    </div>

    <ul :class="['options', { open: isMenuOpen }]">
      <li><RouterLink to="/overview">物價概覽</RouterLink></li>
      <li><RouterLink to="/trending">物價趨勢</RouterLink></li>
      <li><RouterLink to="/news">相關新聞</RouterLink></li>
      <li v-if="!isLoggedIn"><RouterLink to="/login">登入</RouterLink></li>
      <li v-else @click="logout">Hi, {{ userName }}! 登出</li>
    </ul>
  </nav>
</template>

<script>
import { ref, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';

export default {
  name: 'NavBar',
  setup() {
    const isMenuOpen = ref(false);
    const toggleMenu = () => {
      isMenuOpen.value = !isMenuOpen.value;
    };

    const authStore = useAuthStore();
    const isLoggedIn = computed(() => authStore.isLoggedIn);
    const userName = computed(() => authStore.getUserName);

    const logout = () => {
      authStore.logout();
    };

    return {
      isMenuOpen,
      toggleMenu,
      isLoggedIn,
      userName,
      logout
    };
  }
};
</script>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  background-color: #f3f3f3;
  padding: 1.5em;
  height: 4.5em;
  width: 100%;
  align-items: center;
  box-shadow: 0 0 5px #000000;
  position: fixed;
  top: 0;
  z-index: 1000;
}

.title > a {
  font-size: 1.4em;
  font-weight: bold;
  color: #2c3e50 !important;
  text-decoration: none;
}

.hamburger {
  display: none;
  font-size: 1.8em;
  cursor: pointer;
}

.options {
  list-style: none;
  display: flex;
  justify-content: space-around;
}

.options li {
  color: #575B5D;
  margin: 0 0.5em;
  font-size: 1.2em;
}

.options li:hover {
  cursor: pointer;
  font-weight: bold;
}

.options a {
  text-decoration: none;
  color: #575B5D;
}

/* 🔽 RWD 漢堡選單樣式 */
@media (max-width: 768px) {
  .hamburger {
    display: block
  }
  .options {
    position: absolute;
    top: 4.5em;
    left: 0;
    width: 100%;
    flex-direction: column;
    background-color: #f3f3f3;
    display: none;
    padding: 1em;
  }

  .options.open {
    display: flex;
  }

  .options li {
    margin: 0.5em 0;
    text-align: center;
  }
}
</style>