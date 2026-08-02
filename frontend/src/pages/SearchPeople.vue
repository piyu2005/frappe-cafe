<template>
  <PageHeader>
    <Breadcrumbs :items="[{ label: APP_NAME, route: '/' }, { label: 'Search' }]" />
    <Button variant="ghost" icon-left="lucide-pencil" label="Write your story" route="/write" />
  </PageHeader>

  <ScrollArea class="h-[calc(100vh-3rem)]">
    <div class="mx-auto max-w-[760px] px-5 py-8">
      <h1 class="text-3xl font-semibold text-ink-gray-9">Writers at {{ APP_NAME }}</h1>

      <TextInput v-model="query" class="mt-5" placeholder="Search" size="lg">
        <template #prefix>
          <span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" />
        </template>
      </TextInput>

      <LoadingText v-if="people.loading && !people.data" class="mt-6" :lines="4" />

      <div v-else class="mt-4 space-y-1">
        <router-link
          v-for="person in people.data"
          :key="person.name"
          :to="{ name: 'Profile', params: { userId: person.name } }"
          class="flex items-center gap-3 rounded px-2 py-2 hover:bg-surface-gray-1"
        >
          <Avatar :image="person.user_image" :label="person.full_name" size="md" />
          <span class="text-base text-ink-gray-8">{{ person.full_name }}</span>
        </router-link>

        <p v-if="people.data && people.data.length === 0" class="py-10 text-center text-p-base text-ink-gray-6">
          No writers found.
        </p>
      </div>
    </div>
  </ScrollArea>
</template>

<script setup>
import { ref } from 'vue'
import { Avatar, Breadcrumbs, Button, LoadingText, PageHeader, ScrollArea, TextInput, useCall } from 'frappe-ui'
import { APP_NAME } from '@/utils/appName'

const query = ref('')

const people = useCall({
  url: '/api/v2/method/my_new_app.api.list_people',
  params: () => ({ query: query.value }),
  refetch: true,
})
</script>
