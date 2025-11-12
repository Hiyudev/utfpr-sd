"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import {
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { DateTimePicker24h } from "../ui/datetime"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card"
import { PlusIcon } from "lucide-react"

const formSchema = z.object({
    name: z.string().min(2, {
        error: "Nome do produto deve ter no mínimo 2 caracteres.",
    }),
    description: z.string().min(2, {
        error: "A descrição do produto deve ter no mínimo 2 caracteres.",
    }),
    start: z.date(),
    end: z.date(),
    value: z.number().min(0.01, {
        error: "O valor mínimo para um leilão é R$0.01."
    })
})

export function CreationForm() {
    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            name: "",
            description: "",
            value: 0.01,
            start: new Date(),
            end: new Date(),
        },
    })

    function onCreation(values: z.infer<typeof formSchema>) {
        console.log(values)
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Cadastro de leilão</CardTitle>
                <CardDescription>
                    Cadastre o seu leilão.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onCreation)} className="space-y-8">
                        <FormField
                            control={form.control}
                            name="name"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Nome do produto</FormLabel>
                                    <FormControl>
                                        <Input placeholder="Guitarra do Dutra" {...field} />
                                    </FormControl>
                                    <FormDescription>
                                        O nome do produto que será leiloado.
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="description"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Descrição do produto</FormLabel>
                                    <FormControl>
                                        <Input placeholder="Reliquia perdida de Kurt Cobain" {...field} />
                                    </FormControl>
                                    <FormDescription>
                                        A descrição do produto que será leiloado.
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="value"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Valor inicial do produto</FormLabel>
                                    <FormControl>
                                        <Input type="number" step={0.01} {...field} onChange={event => field.onChange(Number(event.target.value))} />
                                    </FormControl>
                                    <FormDescription>
                                        O valor inicial do produto que será leiloado.
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="start"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Quando começa</FormLabel>
                                    <FormControl>
                                        <DateTimePicker24h {...field} />
                                    </FormControl>
                                    <FormDescription>
                                        Quando que começa o leilão.
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="end"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Quando termina</FormLabel>
                                    <FormControl>
                                        <DateTimePicker24h {...field} />
                                    </FormControl>
                                    <FormDescription>
                                        Quando que termina o leilão.
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <Button type="submit">
                            <PlusIcon /> Criar o leilão</Button>
                    </form>
                </Form>
            </CardContent>
        </Card>
    )
}