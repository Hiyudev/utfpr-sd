'use client'

import dynamic from 'next/dynamic';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { ConsultSection } from "@/components/sections/consult_section"
import { CreationForm } from "@/components/sections/creation_section"
import { useState, useEffect } from 'react';
import { Message } from "@/lib/types"
import axios from 'axios';
const ReactJsonView = dynamic(() => import('@microlink/react-json-view'), {
  ssr: false,
});

export default function Home() {
  const [client_id, set_client_id] = useState<string>("");
  const [messages, set_messages] = useState<Message[]>([]);

  async function fetch_client_identification() {
    const response = await axios.get('http://localhost:8888');

    let new_client_id = await response.data;
    new_client_id = new_client_id.replaceAll("\n", "");

    set_client_id(new_client_id);
  }

  useEffect(() => {
    fetch_client_identification();
  }, []);

  useEffect(() => {
    if (client_id.length == 0)
    {
      return;
    }

    // Create an EventSource to listen to SSE events
    const eventSource = new EventSource('http://localhost:8888/events');

    // Handle incoming messages
    eventSource.addEventListener(`notification_${client_id}`, (e) => {
      const data = JSON.parse(e.data) as Message;
      set_messages((prev) => prev.concat(data));
    })

    eventSource.onopen = () => {
        console.log("EventSource connection opened.");
    };

    eventSource.onmessage = (m) => {
      console.log(m.data)
    };

    // Handle errors
    eventSource.onerror = () => {
      eventSource.close();
    };

    // Cleanup on unmount
    return () => {
      eventSource.close();
    };
  }, [client_id])

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex min-h-screen gap-8 w-full max-w-5xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
        <div className="flex flex-col w-full items-center gap-6 text-center sm:items-start sm:text-left">
          <h1 className="max-w-xs text-3xl font-semibold leading-10 tracking-tight text-black dark:text-zinc-50">
            Dashboard
          </h1>

          <p>ID: {client_id}</p>

          <Tabs className="w-full" defaultValue="criar">
            <TabsList>
              <TabsTrigger value="criar">Criar</TabsTrigger>
              <TabsTrigger value="consultar">Consultar</TabsTrigger>
            </TabsList>
            <TabsContent value="criar">
              <CreationForm />
            </TabsContent>
            <TabsContent value="consultar">
              <ConsultSection client_id={client_id} />
            </TabsContent>
          </Tabs>
        </div>

        {messages.length > 0 && (
          <div className="flex flex-col w-full items-center gap-6 text-center sm:items-start sm:text-left">
            <h1 className="max-w-xs text-3xl font-semibold leading-10 tracking-tight text-black dark:text-zinc-50">Últimas notificações</h1>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">Evento</TableHead>
                  <TableHead>Corpo</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {messages.map((message, index) => {
                  const { event_name, ...data } = message;

                  return (
                    <TableRow key={index}>
                      <TableCell>{event_name}</TableCell>
                      <TableCell>
                        <ReactJsonView src={data} theme={"twilight"}/>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </main>
    </div>
  );
}
